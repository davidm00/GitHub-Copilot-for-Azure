"""Retained Blob creation/reuse observations and read-only readiness follow-up."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import stat
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from . import _bootstrap_io as private_io
    from ._progress import Progress, add_progress_argument, reporting
    from . import blob_inventory, blob_source, search_reconcile, source_vector
    from ._common import (
        HelperFailure, SEARCH_AUDIENCE, azure_cli_token, blocked_result, digest,
        emit_result, http_request, reject_secrets,
    )
except ImportError:
    import _bootstrap_io as private_io
    from _progress import Progress, add_progress_argument, reporting
    import blob_inventory, blob_source, search_reconcile, source_vector
    from _common import (
        HelperFailure, SEARCH_AUDIENCE, azure_cli_token, blocked_result, digest,
        emit_result, http_request, reject_secrets,
    )


fail = blob_source._failure
COLLECTIONS = {"datasource": "datasources", "indexer": "indexers",
               "skillset": "skillsets", "index": "indexes"}


def _json(raw):
    def unique(pairs):
        value = {}
        for key, child in pairs:
            if key in value:
                raise ValueError("Duplicate field")
            value[key] = child
        return value
    try:
        value = json.loads(raw, object_pairs_hook=unique)
        json.dumps(value, allow_nan=False, ensure_ascii=False).encode("utf-8")
        if not isinstance(value, dict):
            raise ValueError("Expected object")
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise fail("recheck-evidence-invalid", "Retain bounded, unmodified UTF-8 object evidence.") from exc


def read_private(path):
    path = Path(path)
    private_io.private_directory(str(path.parent))
    try:
        selected = path.lstat()
        if (not stat.S_ISREG(selected.st_mode) or selected.st_nlink != 1
                or getattr(selected, "st_file_attributes", 0) & 0x400):
            raise OSError("Not an ordinary private file")
        if os.name == "nt":
            private_io._windows_private(path)
        elif selected.st_uid != os.getuid() or stat.S_IMODE(selected.st_mode) & 0o077:
            raise OSError("Not private")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (selected.st_dev, selected.st_ino) != (opened.st_dev, opened.st_ino):
                raise OSError("Evidence changed identity")
            raw = handle.read(private_io.MAX_BYTES + 1)
        if len(raw) > private_io.MAX_BYTES:
            raise OSError("Evidence exceeds bound")
        return _json(raw.decode("utf-8"))
    except (OSError, UnicodeError) as exc:
        raise fail("recheck-evidence-unreadable", "Select existing private, unlinked evidence files; no permissions were changed.") from exc


def account_context():
    code, stdout, _ = private_io.run_cli(["account", "show"], 30)
    if code:
        raise fail("recheck-auth-context-unavailable", "Current signed-in CLI context is inaccessible; details withheld.")
    account = _json(stdout)
    user = account.get("user")
    if (account.get("environmentName") != "AzureCloud" or account.get("state") != "Enabled"
            or not isinstance(user, dict) or user.get("type") not in ("user", "servicePrincipal")
            or any(not isinstance(value, str) or not value.strip() for value in
                   (account.get("id"), account.get("tenantId"), user.get("name")))):
        raise fail("recheck-auth-context-unavailable", "An enabled public-cloud tenant/subscription/principal context is required.")
    return digest({key: account[key] for key in ("id", "tenantId", "environmentName")}
                  | {"principal": {"name": user["name"], "type": user["type"]}})


def _supported(plan):
    try:
        source, _ = blob_source._validate_plan(plan)
        ingestion = source["desired"]["azureBlobParameters"]["ingestionParameters"]
    except (KeyError, TypeError, AttributeError, RecursionError) as exc:
        raise fail("recheck-evidence-invalid", "Original Blob creation plan is malformed.") from exc
    if (ingestion.get("contentExtractionMode") not in ("minimal", "standard") or ingestion.get("identity") is not None
            or source["api_version"] not in {"2026-04-01", "2026-08-01-preview"}
            or plan["boundary"]["is_adls"] and source["api_version"] != "2026-08-01-preview"):
        raise fail("recheck-scope-unsupported", "Checkpointing requires supported Blob extraction and provable system-assigned authentication.")
    schedule = ingestion.get("ingestionSchedule")
    if schedule is not None:
        if (not isinstance(schedule, dict) or set(schedule) - {"interval", "startTime"}
                or not isinstance(schedule.get("interval"), str) or not schedule["interval"].strip()):
            raise fail("recheck-schedule-unverified", "Retain the exact admitted interval/startTime schedule; no schedule is inferred or changed.")
        if schedule.get("startTime") is not None:
            blob_source._timestamp(schedule["startTime"])


def _etag(value):
    etag = value.get("@odata.etag") if isinstance(value, dict) else None
    if not isinstance(etag, str) or not etag.strip():
        raise fail("recheck-evidence-missing", "Every source/generated readback requires a nonempty string ETag.")
    return etag


def _processing_readback(plan, current):
    desired = plan["source"]["desired"]["azureBlobParameters"]["ingestionParameters"]
    if desired.get("contentExtractionMode") == "standard":
        ai = desired.get("aiServices")
        if not isinstance(ai, dict) or not isinstance(ai.get("uri"), str) or not ai["uri"].strip():
            raise fail("recheck-processing-unverified", "Standard extraction needs its original CU endpoint evidence.")
        blob_source.verify_content_understanding_readback({"endpoint": ai["uri"]}, current)
    source_vector.verify_source_readback(plan.get("embedding"), current)
    model = desired.get("embeddingModel")
    if model is not None and "embedding" not in plan:
        parameters = model.get("azureOpenAIParameters") if isinstance(model, dict) else None
        if (not isinstance(parameters, dict) or model.get("kind") != "azureOpenAI"
                or any(not isinstance(parameters.get(key), str) or not parameters[key].strip()
                       for key in ("resourceUri", "deploymentId", "modelName"))):
            raise fail("recheck-processing-unverified", "Legacy embedding configuration cannot be verified by this client.")
        source_vector.verify_source_readback({
            "endpoint": parameters["resourceUri"], "deployment": parameters["deploymentId"],
            "model": parameters["modelName"],
        }, current)


def _binding(plan, record, current, generated):
    source = plan["source"]
    observed = {"type": "knowledge-source", "name": source["name"], "etag": _etag(current),
                "definition_digest": digest(search_reconcile._definition(current))}
    if source["action"] == "create":
        blob_source._verify_creation_binding(source, plan["boundary"], current, generated, (plan, record))
    elif (record["verification"]["readback"] != observed
          or not search_reconcile.definitions_match(source["desired"], current)
          or source.get("expected_etag", observed["etag"]) != observed["etag"]):
        raise fail("source-binding-unverified", "Reused source does not match its retained read-only identity/configuration.")
    if (blob_source.generated_resources(current, strict=True) != generated
            or plan.get("expected_generated", generated) != generated):
        raise fail("definition-drift", "Generated source identities changed.")
    blob_source._verify_storage_binding(
        source, plan["boundary"], current, generated,
        lambda: (plan, record) if source["action"] == "create" else None,
    )
    _processing_readback(plan, current)


def _reader(transport, token_provider):
    def tracked(method, url, token, **kwargs):
        try:
            return transport(method, url, token, **kwargs)
        except HelperFailure as failure:
            if failure.request_id:
                ids.append(failure.request_id)
            raise
    read, original_get, ids = source_vector._reader(tracked, token_provider)

    def get(url):
        try:
            return original_get(url)
        except HelperFailure as failure:
            if failure.code in {"vector-resource-missing", "vector-evidence-missing"}:
                missing = failure.code == "vector-resource-missing"
                raise HelperFailure(
                    "recheck-resource-missing" if missing else "recheck-evidence-missing",
                    "An exact original source/generated definition or ETag is unavailable.",
                    blocked_at="verification", status=404 if missing else failure.http_status,
                    request_id=ids[-1] if ids else failure.request_id,
                ) from failure
            raise
    return read, get, ids


def _configuration(plan, creation, generated, get):
    source = plan["source"]
    current = get(search_reconcile.resource_url(source))
    _binding(plan, creation, current, generated)
    names = {item["type"]: item["name"] for item in generated}
    snapshots = {}
    for kind, collection in COLLECTIONS.items():
        name = names[kind]
        url = f"{source['endpoint'].rstrip('/')}/{collection}('{name}')?api-version={source['api_version']}"
        child = get(url)
        etag = _etag(child)
        if child.get("name") != name:
            raise fail("definition-drift", "Generated configuration returned an unrelated identity.")
        if kind == "datasource":
            boundary = plan["boundary"]
            container, credentials = child.get("container"), child.get("credentials")
            connection = credentials.get("connectionString") if isinstance(credentials, dict) else None
            if (child.get("type") != ("adlsgen2" if boundary["is_adls"] else "azureblob")
                    or not isinstance(container, dict) or container.get("name") != boundary["container"]
                    or container.get("query") not in (boundary["prefix"], None if not boundary["prefix"] else boundary["prefix"])
                    or not isinstance(connection, str)
                    or connection.removesuffix(";") != f"ResourceId={boundary['storage_id']}"
                    or child.get("identity") is not None):
                raise fail("source-binding-unverified", "Generated datasource must expose the exact keyless account/container/prefix and system identity; redacted or changed bindings block.")
        if kind == "indexer" and (
            child.get("dataSourceName") != names["datasource"]
            or child.get("targetIndexName") != names["index"]
            or child.get("skillsetName") != names["skillset"]
            or search_reconcile._definition(child.get("schedule")) != search_reconcile._definition(
                source["desired"]["azureBlobParameters"]["ingestionParameters"].get("ingestionSchedule"))
        ):
            raise fail("definition-drift", "Generated indexer binding/schedule differs from the original source.")
        # Keep only integrity observations, never generated credentials or skill text.
        snapshots[kind] = {"etag": etag, "digest": digest(child)}
    refreshed = get(search_reconcile.resource_url(source))
    _binding(plan, creation, refreshed, generated)
    return snapshots


def _baseline_cycle(source, read, token_provider):
    url = search_reconcile.resource_url(source).replace(")?", ")/status?")
    response = read("GET", url, token_provider(SEARCH_AUDIENCE))
    body = response.body
    if response.status != 200 or not isinstance(body, dict) or body.get("kind") != "azureBlob":
        raise HelperFailure("ingestion-inaccessible", "Initial reuse status is unavailable.",
                            blocked_at="verification", status=response.status, request_id=response.request_id)
    last = body.get("lastSynchronizationState")
    if last is None:
        return None
    if not isinstance(last, dict):
        raise fail("ingestion-status-invalid", "Initial reuse synchronization must be an object.")
    cycle = [last.get("startTime"), last.get("endTime")]
    _validate_cycle(cycle)
    return cycle


def _validate_cycle(cycle):
    if cycle is None:
        return
    if not isinstance(cycle, list) or len(cycle) != 2:
        raise fail("recheck-evidence-invalid", "Retain the original observed reuse cycle, not a reconstructed bound.")
    if blob_source._timestamp(cycle[1]) < blob_source._timestamp(cycle[0]):
        raise fail("ingestion-status-invalid", "Initial synchronization interval is invalid.")


class Checkpoint:
    def __init__(self, directory, plan, *, context_provider=account_context):
        _supported(plan)
        self.directory = private_io.private_directory(str(directory))
        self.context_provider = context_provider
        self.context = context_provider()
        self.plan_digest = digest(plan)
        self.operation_id = uuid.uuid4().hex
        self.summary = None
        self.excluded_cycle = None
        self.request_ids = []

    def persist(self, plan, result, generated, not_before, *, token_provider, transport):
        reused = plan["source"]["action"] == "reuse"
        selected, other = ("reused", "created") if reused else ("created", "reused")
        owned = "reused_not_owned" if reused else "run_owned"
        if (digest(plan) != self.plan_digest or len(result["resources"][selected]) != 1
                or result["resources"][other] or result["resources"][selected] != result["ownership"][owned]):
            raise fail("recheck-ownership-unproven", "Retain exact acknowledged creation or read-only reuse; never adopt shared resources.")
        generated = copy.deepcopy(generated)
        creation = {key: copy.deepcopy(result[key]) for key in
                    ("approved_plan", "resources", "verification", "ownership")}
        creation["source"] = {"generated": generated}
        read, get, ids = _reader(transport, token_provider)
        configuration = _configuration(plan, creation, generated, get)
        if reused:
            self.excluded_cycle = _baseline_cycle(plan["source"], read, token_provider)
        if self.context_provider() != self.context:
            raise fail("recheck-auth-context-drift", "CLI context changed during checkpoint capture; no checkpoint was retained.")
        receipt = {
            "schema_version": "1.1" if reused else "1.0", "kind": "blob-readiness-checkpoint",
            "operation_id": self.operation_id, "plan_digest": digest(plan),
            "not_before": not_before.isoformat(), "context_digest": self.context,
            "creation": creation, "configuration": configuration, "request_ids": ids,
        }
        if reused:
            receipt["excluded_cycle"] = self.excluded_cycle
        receipt["integrity"] = digest(receipt)
        path = private_io.private_file(self.directory, self.operation_id + ".blob-readiness.json", receipt)
        self.request_ids = ids
        self.summary = {"operation_id": self.operation_id, "receipt_file": path.name,
                        "evidence_digest": receipt["integrity"], "status": "retained"}


def _document(input_path):
    document = read_private(input_path)
    reject_secrets(document)
    if set(document) != {"schema_version", "plan", "approval"} or document["schema_version"] != "1.0":
        raise fail("recheck-evidence-invalid", "Retain the original source envelope.")
    plan = document["plan"]
    if not isinstance(plan, dict):
        raise fail("recheck-evidence-invalid", "The original plan is unavailable.")
    _supported(plan)
    fingerprint = digest(plan)
    approval = document["approval"]
    if (not isinstance(approval, dict) or set(approval) != {"confirmed", "fingerprint"}
            or type(approval["confirmed"]) is not bool or approval["fingerprint"] != fingerprint
            or plan["source"]["action"] == "create" and approval["confirmed"] is not True):
        raise fail("approval-mismatch", "Retain unchanged creation consent or the fingerprinted read-only reuse plan.")
    return document, plan, fingerprint


def _load(input_path, receipt_path):
    document, plan, fingerprint = _document(input_path)
    receipt = read_private(receipt_path)
    reject_secrets(receipt)
    reused = plan["source"]["action"] == "reuse"
    fields = {"schema_version", "kind", "operation_id", "plan_digest", "not_before",
              "context_digest", "creation", "configuration", "request_ids", "integrity"}
    if reused:
        fields.add("excluded_cycle")
    if (set(receipt) != fields or receipt["schema_version"] != ("1.1" if reused else "1.0")
            or receipt["kind"] != "blob-readiness-checkpoint"
            or receipt["plan_digest"] != fingerprint
            or not isinstance(receipt["operation_id"], str)
            or re.fullmatch("[0-9a-f]{32}", receipt["operation_id"]) is None
            or receipt["integrity"] != digest({k: v for k, v in receipt.items() if k != "integrity"})):
        raise fail("recheck-evidence-invalid", "Original operation/cutoff/checkpoint integrity is missing or changed; never reconstruct it.")
    blob_source._timestamp(receipt["not_before"])
    if reused:
        _validate_cycle(receipt["excluded_cycle"])
    creation = receipt["creation"]
    try:
        observed = creation["verification"]["readback"]
        generated = creation["source"]["generated"]
        expected = {"type": "knowledge-source", "name": plan["source"]["name"],
                    "etag": observed["etag"],
                    "definition_digest": digest(search_reconcile._definition(plan["source"]["desired"]))}
        valid = (
            set(creation) == {"approved_plan", "resources", "verification", "ownership", "source"}
            and set(creation["source"]) == {"generated"}
            and set(creation["verification"]) == {"readback", "absence", "request_ids", "idempotency"}
            and creation["verification"]["absence"] is False
            and creation["verification"]["idempotency"] == "exact readback is zero-write"
            and isinstance(creation["verification"]["request_ids"], list)
            and all(isinstance(item, str) for item in creation["verification"]["request_ids"])
            and creation["approved_plan"] == document["approval"]
            and creation["resources"] == {"created": [] if reused else [expected],
                                          "reused": [expected] if reused else [], "updated": [], "skipped": []}
            and creation["ownership"] == {"run_owned": [] if reused else [expected],
                                          "reused_not_owned": [expected] if reused else [], "owner": plan["owner"]}
            and observed == expected and isinstance(expected["etag"], str) and bool(expected["etag"].strip())
            and generated == blob_source.generated_resources(
                {"azureBlobParameters": {"createdResources": {item["type"]: item["name"] for item in generated}}},
                strict=True,
            )
            and set(receipt["configuration"]) == set(COLLECTIONS)
            and isinstance(receipt["request_ids"], list)
            and all(isinstance(item, str) for item in receipt["request_ids"])
            and isinstance(receipt["context_digest"], str)
            and search_reconcile.SHA256.fullmatch(receipt["context_digest"])
        )
        for item in receipt["configuration"].values():
            valid = valid and set(item) == {"etag", "digest"} and isinstance(item["etag"], str) and bool(item["etag"].strip())
            valid = valid and isinstance(item["digest"], str) and search_reconcile.SHA256.fullmatch(item["digest"])
    except (KeyError, TypeError, AttributeError):
        valid = False
    if not valid:
        raise fail("recheck-ownership-unproven", "Checkpoint must retain exact acknowledged ownership, generated configuration and provenance.")
    return plan, receipt


@reporting("blob-capture")
def capture(input_path, directory, *, token_provider=azure_cli_token, transport=http_request,
            storage_transport=http_request, context_provider=account_context,
            now=lambda: datetime.now(timezone.utc), progress: Progress | None = None):
    progress.update("evidence-validation")
    document, plan, fingerprint = _document(input_path)
    if plan["source"]["action"] != "reuse":
        raise fail("recheck-scope-unsupported", "Fresh capture accepts only a reuse plan; it cannot recover missing original creation proof.")
    progress.update("context-check")
    checkpoint = Checkpoint(directory, plan, context_provider=context_provider)
    cutoff = now()
    progress.update("source-binding")
    _, get, ids = _reader(transport, token_provider)
    current = get(search_reconcile.resource_url(plan["source"]))
    generated = blob_source.generated_resources(current, strict=True)
    result = search_reconcile._completed(
        "blob-readiness-capture", fingerprint, plan["source"], action="reused",
        readback=current, request_ids=ids, absence=False,
    )
    result["approved_plan"] = document["approval"]
    progress.update("blob-inventory")
    inventory = blob_inventory.discover(plan["boundary"], plan["inventory_limits"],
                                       token_provider=token_provider, transport=storage_transport)
    if inventory["inventory_digest"] != plan["inventory_digest"]:
        raise fail("source-drift", "Selected Storage/ACL evidence differs from the reuse plan.")
    result["verification"]["request_ids"].extend(inventory["request_ids"])
    progress.update("checkpoint")
    checkpoint.persist(plan, result, generated, cutoff, token_provider=token_provider, transport=transport)
    return {
        "status": "completed", "outcome": "blob-readiness-capture",
        "recheck_checkpoint": checkpoint.summary, "writes_performed": [],
        "readiness": {"status": "unverified"}, "retrieval": "unverified", "knowledge_base": "not-verified",
        "ownership": result["ownership"], "cleanup": {"separate_confirmation_required": True},
        "read_only_evidence": {"request_ids": result["verification"]["request_ids"] + checkpoint.request_ids},
        "warnings": [blob_source.SNAPSHOT_WARNING, "Fresh reuse observation is not recovered creation ownership or ingestion proof."],
    }


@reporting("blob-recheck")
def recheck(input_path, receipt_path, *, token_provider=azure_cli_token,
            transport=http_request, storage_transport=http_request,
            context_provider=account_context, monotonic=time.monotonic, sleep=time.sleep,
            now=lambda: datetime.now(timezone.utc), progress: Progress | None = None):
    progress.update("evidence-validation")
    plan, receipt = _load(input_path, receipt_path)
    creation = receipt["creation"]
    generated = creation["source"]["generated"]
    readiness = {"status": "unverified"}
    ids = []
    try:
        progress.update("context-check")
        if context_provider() != receipt["context_digest"]:
            raise fail("recheck-auth-context-drift", "Current CLI tenant/subscription/principal differs from the original run; no auth changes were made.")
        read, get, ids = _reader(transport, token_provider)

        def inventory():
            inventory = blob_inventory.discover(
                plan["boundary"], plan["inventory_limits"], token_provider=token_provider,
                transport=storage_transport,
            )
            ids.extend(inventory["request_ids"])
            if inventory["inventory_digest"] != plan["inventory_digest"]:
                raise fail("source-drift", "Selected Storage/ACL evidence differs from original creation.")

        for stage in ("before", "after"):
            if stage == "after":
                progress.update("blob-readback")
                inventory()
            progress.update("source-binding" if stage == "before" else "source-readback")
            configuration = _configuration(plan, creation, generated, get)
            if configuration != receipt["configuration"]:
                raise fail("definition-drift", "Generated configuration/ETags differ from the original checkpoint.")
            if stage == "before":
                progress.update("blob-inventory")
                inventory()
                readiness = blob_source.monitor(
                    plan["source"], not_before=blob_source._timestamp(receipt["not_before"]),
                    limits=plan["poll"], token_provider=token_provider, transport=read,
                    monotonic=monotonic, sleep=sleep, progress=progress,
                    excluded_cycle=receipt.get("excluded_cycle"),
                )
                if readiness["status"] != "verified":
                    raise HelperFailure(
                        readiness["code"], "Original-run ingestion remains unverified.",
                        blocked_at="verification", request_id=readiness.get("request_id"),
                        status=readiness.get("http_status"),
                    )
                cycle = readiness["synchronization"]
                if (cycle["itemsUpdatesProcessed"] == 0 or cycle["itemsSkipped"]
                        or blob_source._timestamp(cycle["endTime"]) > now()):
                    raise fail("ingestion-unverified", "A checkpoint is not prior ingestion proof; nonempty zero-skip completion is required.")
        progress.update("context-readback")
        if context_provider() != receipt["context_digest"]:
            raise fail("recheck-auth-context-drift", "CLI context changed during recheck.")
    except HelperFailure as failure:
        if failure.request_id and failure.request_id not in ids:
            ids.append(failure.request_id)
        safe_failure = HelperFailure(
            failure.code, "Read-only evidence could not verify readiness; service details withheld.",
            blocked_at=failure.blocked_at, status=failure.http_status, request_id=failure.request_id,
        )
        result = blocked_result(safe_failure, outcome="blob-readiness-recheck", fingerprint=None)
        result["safe_next_decision"] = "Preserve original evidence/resources; resolve the blocker without replaying creation or starting an indexer."
        readiness = {**readiness, "status": "unverified"}
    else:
        result = {"status": "completed", "outcome": "blob-readiness-recheck", "writes_performed": []}
    result.update(
        readiness=readiness, retrieval="unverified", knowledge_base="not-verified",
        original_run={"operation_id": receipt["operation_id"], "plan_digest": receipt["plan_digest"],
                      "source_action": plan["source"]["action"],
                      "evidence_digest": receipt["integrity"], "not_before": receipt["not_before"],
                      "request_ids": creation["verification"]["request_ids"],
                      "checkpoint_request_ids": receipt["request_ids"],
                      "original_failure": "not-recorded-by-pre-monitor-checkpoint",
                      "ownership": copy.deepcopy(creation["ownership"]), "generated": generated},
        ownership={"run_owned": [], "reused_not_owned": []},
        read_only_evidence={"request_ids": ids},
        cleanup={"status": "not-requested", "separate_confirmation_required": True},
        warnings=[blob_source.SNAPSHOT_WARNING,
                  "Local checkpoint integrity is not a service signature or new ownership/cleanup authorization."],
    )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--input", type=Path)
    modes.add_argument("--capture", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--receipt-dir", type=Path)
    add_progress_argument(parser)
    args = parser.parse_args(argv)
    if (args.capture and (not args.receipt_dir or args.receipt)
            or args.input and (not args.receipt or args.receipt_dir)):
        parser.error("--capture needs --receipt-dir; --input needs --receipt.")
    try:
        if args.capture:
            result = capture(args.capture, args.receipt_dir, progress=Progress("blob-capture", enabled=args.progress))
        else:
            result = recheck(args.input, args.receipt, progress=Progress("blob-recheck", enabled=args.progress))
    except HelperFailure as failure:
        result = blocked_result(failure, outcome="blob-readiness-recheck", fingerprint=None)
    emit_result(result)
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    sys.exit(main())
