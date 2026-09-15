from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    from ._common import (
        SEARCH_AUDIENCE,
        HelperFailure,
        TokenProvider,
        Transport,
        azure_cli_token,
        blocked_result,
        canonical_bytes,
        digest,
        emit_result,
        http_request,
        is_ambiguous_mutation_failure,
        load_approved_input,
        odata_name,
        reject_secrets,
        require_allowed_fields,
        validate_search_endpoint,
        RESOURCE_ID_CONNECTION,
    )
except ImportError:
    from _common import (  # type: ignore[no-redef]
        SEARCH_AUDIENCE,
        HelperFailure,
        TokenProvider,
        Transport,
        azure_cli_token,
        blocked_result,
        canonical_bytes,
        digest,
        emit_result,
        http_request,
        is_ambiguous_mutation_failure,
        load_approved_input,
        odata_name,
        reject_secrets,
        require_allowed_fields,
        validate_search_endpoint,
        RESOURCE_ID_CONNECTION,
    )


SUPPORTED_API_VERSIONS = {"2026-04-01", "2026-08-01-preview"}
RESOURCE_SEGMENTS = {
    "knowledge-source": "knowledgesources",
    "knowledge-base": "knowledgebases",
}
DYNAMIC_FIELDS = {
    "@odata.context",
    "@odata.etag",
    "currentSynchronizationState",
    "lastSynchronizationState",
    "synchronizationStatus",
    "apiKey",
    "createdResources",
    # Azure Search always returns "<redacted>" for connectionString on GET
    # (secret redaction), never the submitted value, so it can never be
    # compared for exact equality against a desired definition.
    "connectionString",
}
# Endpoint-URI fields where Azure Search's own readback normalization is
# inconsistent (resourceUri loses a trailing slash; aiServices.uri keeps
# whatever was submitted), so both are compared slash-insensitively.
URI_FIELDS = {"resourceUri", "uri"}
SHA256 = re.compile(r"^sha256:[a-f0-9]{64}$")
ENVIRONMENT_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
PLAN_FIELDS = {
    "operation",
    "outcome",
    "plan_kind",
    "resource_type",
    "endpoint",
    "name",
    "api_version",
    "action",
    "desired",
    "source_evidence",
    "verified_source",
    "expected_etag",
    "owned_definition_digest",
    "ai_services_api_key_environment",
    "data_movement",
    "rbac",
    "network",
    "owner",
    "cleanup_approved",
}


def _odata_name(name: Any) -> str:
    return odata_name(name)


def _resource_url(plan: dict[str, Any]) -> str:
    endpoint = validate_search_endpoint(plan.get("endpoint"))
    resource_type = plan.get("resource_type")
    segment = RESOURCE_SEGMENTS.get(resource_type)
    if segment is None:
        raise HelperFailure(
            "resource-type-invalid",
            "resource_type must be knowledge-source or knowledge-base.",
            blocked_at="input-resolution",
        )
    api_version = plan.get("api_version")
    if api_version not in SUPPORTED_API_VERSIONS:
        raise HelperFailure(
            "api-version-invalid",
            "API version must be 2026-04-01 or 2026-08-01-preview.",
            blocked_at="input-resolution",
        )
    return (
        f"{endpoint}/{segment}('{_odata_name(plan.get('name'))}')?"
        + urlencode({"api-version": api_version})
    )


def _definition(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, dict):
        result = {
            child_key: _definition(child, key=child_key)
            for child_key, child in sorted(value.items())
            if child_key not in DYNAMIC_FIELDS and child is not None
        }
        # Preview returns this documented default even when omitted on creation.
        if value.get("kind") == "azureBlob" and result.get("resultsProcessing") == "rerank":
            result.pop("resultsProcessing")
        return {
            child_key: child
            for child_key, child in result.items()
            if child not in ({}, [])
        }
    if isinstance(value, list):
        return [_definition(child) for child in value]
    # Azure Search silently strips a single trailing slash from
    # azureOpenAIParameters.resourceUri on readback (while preserving it
    # verbatim on aiServices.uri), so a byte-exact comparison would
    # false-negative on functionally identical endpoints that differ only
    # by a trailing slash. Normalize both known endpoint-URI field names.
    if (
        key in URI_FIELDS
        and isinstance(value, str)
        and value.endswith("/")
        and len(value) > 1
    ):
        # Remove only one trailing slash; preserve intentional extra
        # slashes (e.g. "https://example.com//") for exact comparison.
        return value[:-1]
    return value


def _get(
    url: str,
    token: str,
    *,
    transport: Transport,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = transport("GET", url, token)
    except HelperFailure as failure:
        if failure.http_status == 404:
            return None, failure.request_id
        raise
    if result.status != 200 or not isinstance(result.body, dict):
        raise HelperFailure(
            "readback-invalid",
            "Search resource readback did not return one JSON object.",
            blocked_at="reconciliation",
            request_id=result.request_id,
            status=result.status,
        )
    return result.body, result.request_id


def _validate_plan(plan: dict[str, Any]) -> None:
    reject_secrets(plan)
    require_allowed_fields(plan, PLAN_FIELDS, label="Search reconciliation plan")
    for field, allowed in (
        ("data_movement", {"boundary", "result"}),
        ("rbac", {"assignments"}),
        ("network", {"posture", "evidence"}),
    ):
        section = plan.get(field)
        if section is not None:
            if not isinstance(section, dict):
                raise HelperFailure(
                    "input-schema-invalid",
                    f"{field} must be an object.",
                    blocked_at="input-resolution",
                )
            require_allowed_fields(section, allowed, label=field)
    operation = plan.get("operation")
    if operation not in {"reconcile", "delete"}:
        raise HelperFailure(
            "operation-invalid",
            "operation must be reconcile or delete.",
            blocked_at="input-resolution",
        )
    if operation == "reconcile":
        if plan.get("cleanup_approved") is not False:
            raise HelperFailure(
                "cleanup-boundary-invalid",
                "A reconciliation plan must set cleanup_approved to false.",
                blocked_at="confirmation",
            )
        desired = plan.get("desired")
        if not isinstance(desired, dict) or desired.get("name") != plan.get("name"):
            raise HelperFailure(
                "desired-definition-invalid",
                "desired must be an object whose name matches the target name.",
                blocked_at="input-resolution",
            )
        if plan.get("resource_type") == "knowledge-source":
            kind = desired.get("kind")
            if kind not in {"file", "azureBlob"}:
                raise HelperFailure(
                    "source-kind-invalid",
                    "Only file and azureBlob knowledge sources are supported.",
                    blocked_at="input-resolution",
                )
            if kind == "file" and plan.get("api_version") != "2026-08-01-preview":
                raise HelperFailure(
                    "api-version-invalid",
                    "This helper uses 2026-08-01-preview for multipart metadata and 200-file inventories. "
                    "The service also supports 2026-05-01-preview minimal; use a compatible client or explicitly approve August.",
                    blocked_at="input-resolution",
                )
            if kind == "file":
                ingestion = (
                    desired.get("fileParameters", {}).get("ingestionParameters", {})
                    if isinstance(desired.get("fileParameters"), dict)
                    else {}
                )
                if not isinstance(ingestion, dict):
                    raise HelperFailure(
                        "desired-definition-invalid",
                        "File ingestionParameters must be an object.",
                        blocked_at="input-resolution",
                    )
                mode = ingestion.get("contentExtractionMode")
                if mode not in {"minimal", "standard"}:
                    raise HelperFailure(
                        "desired-definition-invalid",
                        "File contentExtractionMode must be minimal or standard.",
                        blocked_at="input-resolution",
                    )
                credential_environment = plan.get("ai_services_api_key_environment")
                if mode == "standard":
                    if (
                        not isinstance(credential_environment, str)
                        or ENVIRONMENT_NAME.fullmatch(credential_environment) is None
                        or not isinstance(ingestion.get("aiServices"), dict)
                        or not ingestion["aiServices"].get("uri")
                    ):
                        raise HelperFailure(
                            "credential-channel-invalid",
                            "Standard extraction requires aiServices.uri and an approved API-key environment variable name.",
                            blocked_at="input-resolution",
                        )
                elif credential_environment is not None:
                    raise HelperFailure(
                        "credential-channel-invalid",
                        "Minimal extraction must not declare an AI Services credential channel.",
                        blocked_at="input-resolution",
                    )
            else:
                if plan.get("ai_services_api_key_environment") is not None:
                    raise HelperFailure(
                        "credential-channel-invalid", "Blob ingestion uses keyless dependencies, not File credential channels.",
                        blocked_at="input-resolution",
                    )
                parameters = desired.get("azureBlobParameters")
                evidence = plan.get("source_evidence")
                if isinstance(evidence, dict):
                    require_allowed_fields(
                        evidence,
                        {
                            "verified",
                            "inventory_digest",
                            "path_verified",
                            "acl_verified",
                        },
                        label="Source evidence",
                    )
                if (
                    not isinstance(parameters, dict)
                    or not isinstance(parameters.get("connectionString"), str)
                    or RESOURCE_ID_CONNECTION.fullmatch(
                        parameters["connectionString"]
                    )
                    is None
                    or not isinstance(parameters.get("containerName"), str)
                    or not parameters["containerName"]
                    or "folderPath" not in parameters
                    or not isinstance(parameters.get("isADLSGen2"), bool)
                    or not isinstance(evidence, dict)
                    or evidence.get("verified") is not True
                    or SHA256.fullmatch(str(evidence.get("inventory_digest"))) is None
                ):
                    raise HelperFailure(
                        "source-evidence-invalid",
                        "Blob and ADLS plans require an exact ResourceId boundary and verified immutable inventory evidence.",
                        blocked_at="input-resolution",
                    )
                if parameters["isADLSGen2"] and (
                    evidence.get("path_verified") is not True
                    or evidence.get("acl_verified") is not True
                ):
                    raise HelperFailure(
                        "adls-evidence-unverified",
                        "ADLS reconciliation requires exact path and ACL readback evidence.",
                        blocked_at="reconciliation",
                    )
        if plan.get("resource_type") == "knowledge-base":
            sources = desired.get("knowledgeSources")
            if not isinstance(sources, list) or len(sources) != 1:
                raise HelperFailure(
                    "source-count-invalid",
                    "A knowledge base must name exactly one knowledge source.",
                    blocked_at="input-resolution",
                )
            verified_source = plan.get("verified_source")
            if isinstance(verified_source, dict):
                require_allowed_fields(
                    verified_source,
                    {"name", "verified", "definition_digest"},
                    label="Verified source",
                )
            if (
                not isinstance(sources[0], dict)
                or not isinstance(verified_source, dict)
                or verified_source.get("name") != sources[0].get("name")
                or verified_source.get("verified") is not True
                or SHA256.fullmatch(str(verified_source.get("definition_digest")))
                is None
            ):
                raise HelperFailure(
                    "source-drift",
                    "Knowledge-base reconciliation requires exact verified source readback.",
                    blocked_at="reconciliation",
                )
            _odata_name(verified_source.get("name"))
            if plan.get("api_version") == "2026-04-01":
                preview_fields = {
                    "outputMode",
                    "retrievalReasoningEffort",
                    "retrievalInstructions",
                    "answerInstructions",
                }
                if preview_fields.intersection(desired) or desired.get("models"):
                    raise HelperFailure(
                        "mode-api-mismatch",
                        "GA knowledge bases must omit preview output, reasoning, instruction, and model fields.",
                        blocked_at="input-resolution",
                    )
            else:
                mode = desired.get("outputMode")
                effort = desired.get("retrievalReasoningEffort")
                if (
                    mode not in {"extractiveData", "answerSynthesis"}
                    or not isinstance(effort, dict)
                    or effort.get("kind") not in {"minimal", "low", "medium"}
                    or (effort.get("kind") == "minimal" and mode != "extractiveData")
                    or (
                        (mode == "answerSynthesis" or effort.get("kind") in {"low", "medium"})
                        and (
                            not isinstance(desired.get("models"), list)
                            or len(desired["models"]) != 1
                        )
                    )
                ):
                    raise HelperFailure(
                        "mode-api-mismatch",
                        "Preview knowledge-base output mode, reasoning effort, and model selection are inconsistent.",
                        blocked_at="input-resolution",
                    )
    else:
        if plan.get("plan_kind") != "cleanup" or plan.get("cleanup_approved") is not True:
            raise HelperFailure(
                "cleanup-approval-mismatch",
                "Delete requires a separate cleanup plan with cleanup_approved true.",
                blocked_at="confirmation",
            )
        if not isinstance(plan.get("owned_definition_digest"), str):
            raise HelperFailure(
                "ownership-unproven",
                "Delete requires the approved owned definition digest.",
                blocked_at="reconciliation",
            )


def resource_url(plan: dict[str, Any]) -> str:
    """Validate and address the exact selected Search resource."""
    return _resource_url(plan)


def read_resource(
    url: str, token: str, *, transport: Transport
) -> tuple[dict[str, Any] | None, str | None]:
    """Read one identity; only a definitive 404 means absent."""
    return _get(url, token, transport=transport)


def definitions_match(desired: dict[str, Any], current: dict[str, Any]) -> bool:
    return _definition(desired) == _definition(current)


def execute(
    document: dict[str, Any],
    *,
    token_provider: TokenProvider = azure_cli_token,
    transport: Transport = http_request,
) -> dict[str, Any]:
    plan = document["plan"]
    fingerprint = document["_computed_fingerprint"]
    _validate_plan(plan)
    url = _resource_url(plan)
    token = token_provider(SEARCH_AUDIENCE)
    current, initial_request_id = _get(url, token, transport=transport)
    operation = plan["operation"]
    outcome = str(plan.get("outcome") or f"search-{operation}")
    owner = plan.get("owner")

    if operation == "delete":
        if current is None:
            return _completed(
                outcome,
                fingerprint,
                plan,
                action="skipped",
                readback=None,
                request_ids=[initial_request_id],
                absence=True,
            )
        current_definition = _definition(current)
        if digest(current_definition) != plan["owned_definition_digest"]:
            raise HelperFailure(
                "ownership-unproven",
                "Current definition no longer matches the approved owned definition.",
                blocked_at="reconciliation",
            )
        expected_etag = plan.get("expected_etag")
        if not expected_etag or current.get("@odata.etag") != expected_etag:
            raise HelperFailure(
                "definition-drift",
                "Current ETag does not match the approved cleanup plan.",
                blocked_at="reconciliation",
            )
        try:
            result = transport(
                "DELETE",
                url,
                token,
                headers={"If-Match": expected_etag},
            )
        except HelperFailure as failure:
            if failure.http_status == 404:
                return _completed(
                    outcome,
                    fingerprint,
                    plan,
                    action="skipped",
                    readback=None,
                    request_ids=[initial_request_id, failure.request_id],
                    absence=True,
                )
            if not is_ambiguous_mutation_failure(failure):
                raise
            return _recover_ambiguous_delete(
                outcome,
                fingerprint,
                plan,
                url,
                token,
                initial_request_id,
                failure,
                transport=transport,
            )
        if result.status not in {200, 204}:
            if result.status == 404:
                return _completed(
                    outcome,
                    fingerprint,
                    plan,
                    action="skipped",
                    readback=None,
                    request_ids=[initial_request_id, result.request_id],
                    absence=True,
                )
            if result.status in {408, 429} or result.status >= 500:
                return _recover_ambiguous_delete(
                    outcome,
                    fingerprint,
                    plan,
                    url,
                    token,
                    initial_request_id,
                    HelperFailure(
                        "delete-outcome-ambiguous",
                        f"Delete returned ambiguous HTTP {result.status}.",
                        blocked_at="execution",
                        request_id=result.request_id,
                        status=result.status,
                        partial=True,
                    ),
                    transport=transport,
                )
            raise HelperFailure(
                "delete-failed",
                f"Delete returned unexpected HTTP {result.status}.",
                blocked_at="execution",
                request_id=result.request_id,
                status=result.status,
            )
        write = {"action": "deleted", "name": plan["name"]}
        try:
            after, verify_request_id = _get(url, token, transport=transport)
        except HelperFailure as failure:
            raise HelperFailure(
                failure.code,
                failure.message,
                blocked_at=failure.blocked_at,
                writes=[write, *failure.writes],
                resources_remaining=[_target_identity(plan)],
                request_id=failure.request_id,
                status=failure.http_status,
                partial=True,
            ) from failure
        if after is not None:
            raise HelperFailure(
                "absence-unverified",
                "The exact resource still exists after delete.",
                blocked_at="verification",
                writes=[write],
                resources_remaining=[_target_identity(plan)],
                request_id=verify_request_id,
                partial=True,
            )
        return _completed(
            outcome,
            fingerprint,
            plan,
            action="deleted",
            readback=None,
            request_ids=[initial_request_id, result.request_id, verify_request_id],
            absence=True,
        )

    source_request_id = None
    if plan["resource_type"] == "knowledge-base":
        verified_source = plan["verified_source"]
        source_url = _resource_url({
            **plan, "resource_type": "knowledge-source", "name": verified_source["name"],
        })
        source, source_request_id = _get(source_url, token, transport=transport)
        if source is None or digest(_definition(source)) != verified_source["definition_digest"]:
            raise HelperFailure(
                "source-drift",
                "The source is absent or its current definition differs from the approved source.",
                blocked_at="reconciliation",
                request_id=source_request_id,
            )

    desired = plan["desired"]
    if current is not None and _definition(desired) == _definition(current):
        if (
            plan.get("action") == "reuse"
            and plan.get("expected_etag") is not None
            and current.get("@odata.etag") != plan["expected_etag"]
        ):
            raise HelperFailure(
                "definition-drift",
                "Current ETag does not match the approved reuse plan.",
                blocked_at="reconciliation",
            )
        return _completed(
            outcome,
            fingerprint,
            plan,
            action="reused",
            readback=current,
            request_ids=[initial_request_id, source_request_id],
            absence=False,
        )

    action = plan.get("action")
    headers = {
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if current is None:
        if action != "create":
            raise HelperFailure(
                "target-absent",
                "The approved update target does not exist.",
                blocked_at="reconciliation",
            )
        headers["If-None-Match"] = "*"
        completed_action = "created"
    else:
        if action != "update":
            raise HelperFailure(
                "definition-conflict",
                "An existing non-equivalent resource cannot be overwritten by this plan.",
                blocked_at="reconciliation",
            )
        expected_etag = plan.get("expected_etag")
        if not expected_etag or current.get("@odata.etag") != expected_etag:
            raise HelperFailure(
                "definition-drift",
                "Current ETag does not match the approved update plan.",
                blocked_at="reconciliation",
            )
        headers["If-Match"] = expected_etag
        completed_action = "updated"

    request_desired = copy.deepcopy(desired)
    credential_environment = plan.get("ai_services_api_key_environment")
    if credential_environment is not None:
        secret = os.environ.get(credential_environment)
        if not secret:
            raise HelperFailure(
                "credential-unavailable",
                "The approved AI Services credential environment variable is unset.",
                blocked_at="execution",
            )
        request_desired["fileParameters"]["ingestionParameters"]["aiServices"][
            "apiKey"
        ] = secret
    try:
        result = transport(
            "PUT",
            url,
            token,
            body=canonical_bytes(request_desired),
            headers=headers,
        )
    except HelperFailure as failure:
        if not is_ambiguous_mutation_failure(failure):
            raise
        return _recover_ambiguous_put(
            outcome,
            fingerprint,
            plan,
            url,
            token,
            initial_request_id,
            completed_action,
            failure,
            transport=transport,
            source_request_id=source_request_id,
        )
    if result.status not in {200, 201}:
        if result.status in {408, 429} or result.status >= 500:
            return _recover_ambiguous_put(
                outcome,
                fingerprint,
                plan,
                url,
                token,
                initial_request_id,
                completed_action,
                HelperFailure(
                    "mutation-outcome-ambiguous",
                    f"Create or update returned ambiguous HTTP {result.status}.",
                    blocked_at="execution",
                    request_id=result.request_id,
                    status=result.status,
                    partial=True,
                ),
                transport=transport,
                source_request_id=source_request_id,
            )
        raise HelperFailure(
            "mutation-failed",
            f"Create or update returned unexpected HTTP {result.status}.",
            blocked_at="execution",
            request_id=result.request_id,
            status=result.status,
        )
    write = {"action": completed_action, "name": plan["name"]}
    try:
        after, verify_request_id = _get(url, token, transport=transport)
    except HelperFailure as failure:
        raise HelperFailure(
            failure.code,
            failure.message,
            blocked_at=failure.blocked_at,
            writes=[write, *failure.writes],
            resources_remaining=[_target_identity(plan)],
            request_id=failure.request_id,
            status=failure.http_status,
            partial=True,
        ) from failure
    if after is None or _definition(desired) != _definition(after):
        raise HelperFailure(
            "readback-mismatch",
            "Readback does not contain the approved definition.",
            blocked_at="verification",
            writes=[write],
            resources_remaining=[_target_identity(plan)],
            request_id=verify_request_id,
            partial=True,
        )
    return _completed(
        outcome,
        fingerprint,
        plan,
        action=completed_action,
        readback=after,
        request_ids=[initial_request_id, source_request_id, result.request_id, verify_request_id],
        absence=False,
    )


def _target_identity(plan: dict[str, Any]) -> dict[str, Any]:
    return {"type": plan["resource_type"], "name": plan["name"]}


def _recover_ambiguous_put(
    outcome: str,
    fingerprint: str,
    plan: dict[str, Any],
    url: str,
    token: str,
    initial_request_id: str | None,
    completed_action: str,
    failure: HelperFailure,
    *,
    transport: Transport,
    source_request_id: str | None = None,
) -> dict[str, Any]:
    identity = _target_identity(plan)
    try:
        after, verify_request_id = _get(url, token, transport=transport)
    except HelperFailure as readback_failure:
        raise HelperFailure(
            "mutation-outcome-ambiguous",
            "Create or update outcome and same-identity readback are ambiguous.",
            blocked_at="verification",
            resources_remaining=[identity],
            request_id=readback_failure.request_id or failure.request_id,
            status=failure.http_status,
            partial=True,
        ) from readback_failure
    if after is None or _definition(plan["desired"]) != _definition(after):
        raise HelperFailure(
            "mutation-outcome-ambiguous",
            "Same-identity readback did not prove the approved create or update.",
            blocked_at="verification",
            resources_remaining=[identity],
            request_id=verify_request_id or failure.request_id,
            status=failure.http_status,
            partial=True,
        )
    return _completed(
        outcome,
        fingerprint,
        plan,
        action=completed_action,
        readback=after,
        request_ids=[
            initial_request_id,
            source_request_id,
            failure.request_id,
            verify_request_id,
        ],
        absence=False,
    )


def _recover_ambiguous_delete(
    outcome: str,
    fingerprint: str,
    plan: dict[str, Any],
    url: str,
    token: str,
    initial_request_id: str | None,
    failure: HelperFailure,
    *,
    transport: Transport,
) -> dict[str, Any]:
    identity = _target_identity(plan)
    try:
        after, verify_request_id = _get(url, token, transport=transport)
    except HelperFailure as readback_failure:
        raise HelperFailure(
            "delete-outcome-ambiguous",
            "Delete outcome and same-identity readback are ambiguous.",
            blocked_at="verification",
            resources_remaining=[identity],
            request_id=readback_failure.request_id or failure.request_id,
            status=failure.http_status,
            partial=True,
        ) from readback_failure
    if after is not None:
        raise HelperFailure(
            "delete-outcome-ambiguous",
            "Same-identity readback still found the resource after an ambiguous delete.",
            blocked_at="verification",
            resources_remaining=[identity],
            request_id=verify_request_id or failure.request_id,
            status=failure.http_status,
            partial=True,
        )
    return _completed(
        outcome,
        fingerprint,
        plan,
        action="deleted",
        readback=None,
        request_ids=[
            initial_request_id,
            failure.request_id,
            verify_request_id,
        ],
        absence=True,
    )


def _completed(
    outcome: str,
    fingerprint: str,
    plan: dict[str, Any],
    *,
    action: str,
    readback: dict[str, Any] | None,
    request_ids: list[str | None],
    absence: bool,
) -> dict[str, Any]:
    resource = {
        "type": plan["resource_type"],
        "name": plan["name"],
        "etag": readback.get("@odata.etag") if readback else None,
        "definition_digest": digest(_definition(readback)) if readback else None,
    }
    resources = {"created": [], "reused": [], "updated": [], "skipped": []}
    if action in resources:
        resources[action].append(resource)
    elif action == "deleted":
        resources["deleted"] = [resource]
    return {
        "status": "completed",
        "outcome": outcome,
        "approved_plan": {"fingerprint": fingerprint, "confirmed": True},
        "resources": resources,
        "api_contracts": [
            {
                "operation": plan["operation"],
                "version": plan["api_version"],
                "preview": plan["api_version"].endswith("-preview"),
            }
        ],
        "data_movement": plan.get("data_movement", {"boundary": None, "result": "none"}),
        "auth": {"mode": "entra-user", "principals": []},
        "rbac": plan.get("rbac", {"assignments": []}),
        "network": plan.get("network", {"posture": "preserved", "evidence": None}),
        "verification": {
            "readback": resource,
            "absence": absence,
            "request_ids": [item for item in request_ids if item],
            "idempotency": "exact readback is zero-write",
        },
        "warnings": [],
        "ownership": {
            "run_owned": [resource] if action in {"created", "deleted"} else [],
            "reused_not_owned": [resource] if action == "reused" else [],
            "owner": plan.get("owner"),
        },
        "cleanup": {
            "status": (
                "completed"
                if plan["operation"] == "delete" and absence
                else "not-requested"
            ),
            "separate_confirmation_required": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    fingerprint: str | None = None
    owner: Any = None
    outcome = "search-resource-reconciliation"
    try:
        document, plan, fingerprint = load_approved_input(args.input)
        document["_computed_fingerprint"] = fingerprint
        owner = plan.get("owner")
        outcome = str(plan.get("outcome") or outcome)
        result = execute(document)
    except HelperFailure as failure:
        result = blocked_result(
            failure,
            outcome=outcome,
            fingerprint=fingerprint,
            owner=owner,
        )
        emit_result(result)
        return 3 if result["status"] == "partial" else 2
    emit_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
