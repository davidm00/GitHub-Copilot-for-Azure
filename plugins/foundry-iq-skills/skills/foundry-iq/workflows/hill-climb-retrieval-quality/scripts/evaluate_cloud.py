"""Submit captured workload rows to Foundry cloud evaluation after explicit review."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import urlsplit

from evaluation_contract import (ContractError, PROFILES, build_request, digest,
                                 finite_number, nonblank, read_rows, validate_rows)


METRICS = {name: (name,) for name in ("groundedness", "relevance", "retrieval", "response_completeness")}
METRICS["document_retrieval"] = (
    "ndcg@3", "xdcg@3", "fidelity", "top1_relevance", "top3_max_relevance", "holes", "holes_ratio")
DISPLAY_NAMES = {"Groundedness": "groundedness", "Relevance": "relevance", "Retrieval": "retrieval",
                 "Response Completeness": "response_completeness", "Document Retrieval": "document_retrieval"}


def as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise ContractError("Malformed cloud response")


def validate_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    if (parsed.scheme != "https" or not parsed.hostname
            or not parsed.hostname.endswith(".services.ai.azure.com")
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.port not in (None, 443)
            or not parsed.path.startswith("/api/projects/")
            or len(parsed.path.strip("/").split("/")) != 3):
        raise ContractError("Use the approved Azure public-cloud Foundry project endpoint")


def required_metrics(profile: str, metric_contract: Any = None) -> dict[str, list[str]]:
    if profile not in PROFILES:
        raise ContractError("Unknown evaluation profile")
    expected = ({name: list(METRICS[name]) for name in PROFILES[profile]}
                if metric_contract is None else metric_contract)
    if not isinstance(expected, dict) or set(expected) != set(PROFILES[profile]) or any(
            not isinstance(values, list) or not values or not all(nonblank(value) for value in values)
            or len(set(values)) != len(values) for values in expected.values()):
        raise ContractError("Freeze the selected evaluator metric contract before submission")
    return expected


def verify_definition(request: dict[str, Any], evaluation: dict[str, Any]) -> None:
    expected_schema = request["data_source_config"]
    returned_schema = evaluation.get("data_source_config")
    if (not isinstance(returned_schema, dict)
            or returned_schema.get("type") != expected_schema["type"]
            or returned_schema.get("include_sample_schema", False)
            != expected_schema.get("include_sample_schema", False)):
        raise ContractError("Cloud evaluation schema changed")
    schemas = [returned_schema.get("item_schema")]
    for key in ("schema", "schema_"):
        envelope = returned_schema.get(key)
        if isinstance(envelope, dict):
            schemas.append(envelope.get("item"))
    populated = [schema for schema in schemas if schema is not None and schema != {}]
    if not populated or any(digest(schema) != digest(expected_schema["item_schema"]) for schema in populated):
        raise ContractError("Cloud evaluation item schema changed")
    criteria = evaluation.get("testing_criteria")
    expected = {criterion["name"]: criterion for criterion in request["testing_criteria"]}
    if not isinstance(criteria, list) or len(criteria) != len(expected):
        raise ContractError("Cloud evaluator definition changed")
    observed: set[str] = set()
    for criterion in criteria:
        if not isinstance(criterion, dict) or criterion.get("name") not in expected:
            raise ContractError("Cloud evaluator definition changed")
        name = criterion["name"]
        if name in observed or any(digest(criterion.get(key)) != digest(value)
                                   for key, value in expected[name].items()):
            raise ContractError("Cloud evaluator mapping or judge binding changed")
        observed.add(name)


def datasource_row(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("Malformed cloud datasource row")
    if "id" in value and "query" in value:
        return value
    nested = value.get("item")
    if not isinstance(nested, dict):
        raise ContractError("Cloud datasource has no original item")
    for key, mapped_value in value.items():
        if key == "item":
            continue
        if not key.startswith("item."):
            raise ContractError("Unexpected cloud datasource envelope")
        original = nested
        for field in key[5:].split("."):
            if not isinstance(original, dict) or field not in original:
                raise ContractError("Cloud mapping does not resolve to original row")
            original = original[field]
        if original != mapped_value:
            raise ContractError("Cloud mapping disagrees with original row")
    return nested


def verify_results(rows: list[dict[str, Any]], items: list[dict[str, Any]], *,
                   profile: str, eval_id: str, run_id: str,
                   metric_contract: dict[str, list[str]] | None = None) -> dict[str, Any]:
    validate_rows(rows, profile)
    expected = required_metrics(profile, metric_contract)
    expected_keys = {(name, metric) for name, metrics in expected.items() for metric in metrics}
    if len(rows) != len(items):
        raise ContractError("Returned row count differs from the frozen set")
    if any(not isinstance(item, dict) or not isinstance(item.get("datasource_item"), dict) for item in items):
        raise ContractError("Malformed cloud datasource row")
    if Counter(digest(row) for row in rows) != Counter(digest(datasource_row(item.get("datasource_item"))) for item in items):
        raise ContractError("Missing, replaced or duplicate cloud rows")
    observed_ids: set[str] = set()
    scores: dict[str, list[float]] = {name + "/" + metric: [] for name, metric in expected_keys}
    normalized = []
    for item in items:
        identifier = item.get("id")
        if (not nonblank(identifier) or identifier in observed_ids or item.get("error") is not None
                or item.get("eval_id") != eval_id or item.get("run_id") != run_id
                or item.get("status") not in (None, "pass", "fail", "completed")):
            raise ContractError("Invalid cloud output identity or row error")
        observed_ids.add(identifier)
        sample = item.get("sample")
        if sample is not None and (not isinstance(sample, dict) or sample.get("error") is not None
                                   or sample.get("finish_reason") not in (None, "", "stop")):
            raise ContractError("Cloud sample error")
        results = item.get("results")
        if not isinstance(results, list):
            raise ContractError("Missing metric results")
        metrics = {}
        for result in results:
            if not isinstance(result, dict):
                raise ContractError("Malformed metric result")
            name = DISPLAY_NAMES.get(result.get("name"), result.get("name"))
            metric = result.get("metric", name)
            key = (name, metric)
            if key not in expected_keys or key in metrics:
                raise ContractError("Unexpected, missing or duplicate evaluator metric")
            if (result.get("type") != "azure_ai_evaluator" or result.get("error") is not None
                    or not finite_number(result.get("score")) or type(result.get("passed")) is not bool
                    or (name != "document_retrieval" and not nonblank(result.get("reason")))):
                raise ContractError("Incomplete or nonfinite cloud score")
            metrics[key] = {"score": result["score"], "passed": result["passed"],
                            "reason": result.get("reason")}
            scores[name + "/" + metric].append(float(result["score"]))
        if set(metrics) != expected_keys:
            raise ContractError("A required evaluator metric is missing")
        passed = all(metric["passed"] for metric in metrics.values())
        if item.get("status") in ("pass", "fail") and item["status"] != ("pass" if passed else "fail"):
            raise ContractError("Row status contradicts metric outcomes")
        normalized.append({"id": datasource_row(item["datasource_item"])["id"], "passed": passed,
                           "metrics": {name + "/" + metric: value for (name, metric), value in metrics.items()}})
    return {"integrity": "valid", "quality_verdict": "not_assessed", "rows": normalized,
            "failed_quality_rows": sum(not row["passed"] for row in normalized),
            "metrics": {key: {"count": len(values), "mean": sum(values) / len(values)}
                        for key, values in scores.items()}}


def judge_usage(items: list[dict[str, Any]], profile: str) -> dict[str, Any]:
    if profile == "ranking":
        return {"status": "not_applicable", "reason": "Server-side deterministic scoring; no LLM judge"}
    samples = [result.get("sample") for item in items for result in item["results"]]
    models: dict[str | None, list[dict[str, Any]]] = {}
    for sample in samples:
        sample = sample if isinstance(sample, dict) else {}
        model = sample.get("model") if nonblank(sample.get("model")) else None
        usage = sample.get("usage")
        models.setdefault(model, []).append(usage if isinstance(usage, dict) else {})
    by_model = []
    for model, values in models.items():
        entry: dict[str, Any] = {"model": model, "samples": len(values)}
        for field in ("prompt_tokens", "completion_tokens"):
            known = [value[field] for value in values if type(value.get(field)) is int and value[field] >= 0]
            entry[field] = sum(known) if len(known) == len(values) else None
            entry["known_" + field] = sum(known) if known else None
            entry["missing_" + field + "_samples"] = len(values) - len(known)
        by_model.append(entry)
    complete = bool(samples) and all(entry["model"] is not None
                                    and entry["prompt_tokens"] is not None
                                    and entry["completion_tokens"] is not None for entry in by_model)
    return {"status": "complete" if complete else "incomplete", "samples": len(samples),
            "prompt_tokens": sum(entry["prompt_tokens"] for entry in by_model) if complete else None,
            "completion_tokens": sum(entry["completion_tokens"] for entry in by_model) if complete else None,
            "by_model": by_model,
            "limitation": "Observed judge tokens, not price or complete billing; input includes any cached tokens"}


def write_json(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def runtime_provenance() -> dict[str, Any]:
    packages = {}
    for name in ("azure-ai-projects", "azure-identity", "openai"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    scripts = Path(__file__).resolve().parent
    return {"python": sys.version, "packages": packages,
            "scripts": {name: digest((scripts / name).read_text(encoding="utf-8"))
                        for name in ("evaluation_contract.py", "evaluate_cloud.py")}}


def run_cloud(client: Any, *, rows: list[dict[str, Any]], plan: dict[str, Any],
              output: Path, clock=time.monotonic, wait=time.sleep) -> dict[str, Any]:
    request = plan["request"]
    profile = plan["profile"]
    timeout = plan["timeout_seconds"]
    validate_endpoint(plan["project_endpoint"])
    validate_rows(rows, profile)
    required_metrics(profile, plan.get("metric_contract"))
    source = request.get("data_source", {}).get("source", {})
    criteria = request.get("testing_criteria", [])
    judge = criteria[0].get("initialization_parameters", {}).get("deployment_name") if criteria else None
    expected_request = build_request(rows, profile=profile, judge=judge,
                                     dataset_id=source.get("id") if source.get("type") == "file_id" else None)
    if request != expected_request or plan.get("rows_sha256") != digest(rows):
        raise ContractError("Request does not match frozen captured rows and evaluator profile")
    if not finite_number(timeout) or timeout <= 0:
        raise ContractError("A positive execution deadline is required")
    output.mkdir(parents=False, exist_ok=False)
    write_json(output / "plan.json", plan)
    receipt: dict[str, Any] = {
        "schema_version": "1.0", "execution_mode": "captured_rows_cloud",
        "started_at": datetime.now(timezone.utc).isoformat(), "plan_sha256": digest(plan),
        "dataset_sha256": digest(rows), "project_endpoint": plan["project_endpoint"],
        "profile": profile, "expected_rows": len(rows), "integrity": "incomplete",
        "quality_verdict": "not_assessed", "eval_id": None, "run_id": None,
        "report_url": None, "judge_usage": None, "total_cost": None,
        "target_latency_seconds": None, "target_usage": None, "search_count": None,
        "measurement_limitations": {
            "judge_usage": "No verified evaluator output usage yet",
            "target_latency_seconds": "Precomputed rows do not contain target timing; retain the capture ledger",
            "target_usage": "Target activity is separate from cloud judge output; retain the capture ledger",
            "search_count": "Precomputed rows do not expose Search activity",
            "total_cost": "Observed tokens lack complete, attributable billing and verified component prices",
        },
        "cost_limitation": "No complete attributable billing telemetry in this response",
    }
    started = clock()
    items: list[dict[str, Any]] = []

    def bounded_client():
        remaining = timeout - (clock() - started)
        if remaining <= 0:
            raise TimeoutError("Cloud deadline reached; remote run may still be active")
        return client.with_options(max_retries=0, timeout=min(60, remaining))

    stage = "create-evaluation"
    try:
        metadata = {"scenario": "retrieval-quality", "plan_sha256": digest(plan),
                    "dataset_sha256": digest(rows), "profile": profile}
        evaluation = as_dict(bounded_client().evals.create(
            name=plan["name"], metadata=metadata,
            data_source_config=request["data_source_config"], testing_criteria=request["testing_criteria"]))
        if not nonblank(evaluation.get("id")):
            raise ContractError("Evaluation creation returned no identity")
        receipt["eval_id"] = evaluation["id"]
        write_json(output / "evaluation.json", evaluation)
        stage = "verify-definition"
        verify_definition(request, evaluation)
        receipt["evaluation_definition_sha256"] = digest(evaluation)
        stage = "create-run"
        run = as_dict(bounded_client().evals.runs.create(
            eval_id=evaluation["id"], name=plan["name"], metadata=metadata,
            data_source=request["data_source"]))
        if not nonblank(run.get("id")):
            raise ContractError("Run creation returned no identity")
        receipt["run_id"] = run["id"]
        write_json(output / "submission.json", run)
        stage = "poll-run"
        with (output / "status.jsonl").open("x", encoding="utf-8") as status_stream:
            while True:
                run = as_dict(bounded_client().evals.runs.retrieve(eval_id=receipt["eval_id"], run_id=receipt["run_id"]))
                if run.get("id") != receipt["run_id"] or run.get("eval_id") != receipt["eval_id"]:
                    raise ContractError("Cloud run identity changed")
                status_stream.write(json.dumps({"status": run.get("status"), "elapsed_seconds": clock() - started}) + "\n")
                status_stream.flush()
                if run.get("status") in {"completed", "failed", "error", "canceled", "cancelled"}:
                    break
                wait(min(5, max(0, timeout - (clock() - started))))
        write_json(output / "run.json", run)
        receipt["service_status"] = run.get("status")
        if run.get("status") != "completed" or run.get("error") is not None:
            raise ContractError("Cloud run did not complete successfully")
        report = urlsplit(run.get("report_url") or "")
        if (report.scheme != "https" or report.hostname != "ai.azure.com"
                or report.username or report.password or report.port not in (None, 443)):
            raise ContractError("Missing supported service-returned report URL")
        receipt["report_url"] = run["report_url"]
        stage = "verify-source"
        if digest(run.get("data_source")) != digest(request["data_source"]):
            raise ContractError("Cloud run data source changed")
        stage = "read-results"
        receipt["output_readback_attempts"] = 0
        while True:
            items = []
            cursor = None
            seen_cursors: set[str] = set()
            receipt["output_readback_attempts"] += 1
            attempt = output / f"output-readback-{receipt['output_readback_attempts']:03d}.jsonl"
            with attempt.open("x", encoding="utf-8") as page_stream:
                while True:
                    paging = {"after": cursor} if cursor is not None else {}
                    page = as_dict(bounded_client().evals.runs.output_items.list(
                        eval_id=receipt["eval_id"], run_id=receipt["run_id"], limit=100, order="asc", **paging))
                    page_stream.write(json.dumps(page, ensure_ascii=False, allow_nan=False) + "\n")
                    page_stream.flush()
                    data = page.get("data")
                    if not isinstance(data, list) or page.get("has_more") not in (None, True, False):
                        raise ContractError("Malformed cloud result page")
                    for raw in data:
                        items.append(as_dict(raw))
                        if len(items) > len(rows) or clock() - started >= timeout:
                            raise ContractError("Extra output rows or result-readback deadline exceeded")
                    if page.get("has_more") is False or (not data and page.get("has_more") is not True):
                        break
                    cursor = page.get("last_id") or (data[-1].get("id") if data else None)
                    if not nonblank(cursor) or cursor in seen_cursors:
                        raise ContractError("Result pagination did not advance")
                    seen_cursors.add(cursor)
            if len(items) == len(rows):
                break
            counts = run.get("result_counts", {})
            if (type(counts.get("total")) is not int or counts["total"] != len(rows)
                    or type(counts.get("errored")) is not int or counts["errored"] != 0):
                raise ContractError("Incomplete outputs do not match a successfully completed cloud population")
            remaining = timeout - (clock() - started)
            if remaining <= 0:
                raise TimeoutError("Cloud output publication deadline reached; inspect retained readbacks")
            wait(min(5, remaining))
        stage = "verify-results"
        verified = verify_results(rows, items, profile=profile, eval_id=receipt["eval_id"],
                                  run_id=receipt["run_id"], metric_contract=plan.get("metric_contract"))
        counts = run.get("result_counts")
        failures = verified["failed_quality_rows"]
        if (not isinstance(counts, dict) or any(type(counts.get(key)) is not int
                for key in ("total", "passed", "failed", "errored"))
                or counts["total"] != len(rows) or counts["errored"] != 0
                or counts["failed"] != failures or counts["passed"] != len(rows) - failures):
            raise ContractError("Service counts disagree with retained row results")
        receipt.update(verified)
        receipt["judge_usage"] = judge_usage(items, profile)
        receipt["measurement_limitations"]["judge_usage"] = receipt["judge_usage"].get("limitation", receipt["judge_usage"].get("reason"))
    except Exception as error:
        receipt.update(integrity="invalid", failed_stage=stage, error_type=type(error).__name__,
                       recovery="Inspect retained evidence; do not resubmit or clean up automatically")
    if receipt.get("output_readback_attempts"):
        with (output / "output-items.jsonl").open("x", encoding="utf-8") as item_stream:
            for item in items:
                item_stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
    receipt["evaluation_wall_seconds"] = clock() - started
    receipt["completed_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "result.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--rows", required=True, type=Path)
    parser.add_argument("--project-endpoint", required=True)
    parser.add_argument("--profile", choices=PROFILES, default="answer")
    parser.add_argument("--judge")
    parser.add_argument("--dataset-id", help="Separately verified registered dataset ID; otherwise inline")
    parser.add_argument("--name", default="retrieval-quality-baseline")
    parser.add_argument("--metric-contract", type=Path, help="Verified evaluator metric names from catalog/probe")
    parser.add_argument("--timeout-seconds", type=float, default=600)
    parser.add_argument("--output", required=True, type=Path, help="New private artifact directory; parent must exist")
    parser.add_argument("--approve-plan", help="Approved digest from the dry-run; absence means no remote calls")
    args = parser.parse_args()
    validate_endpoint(args.project_endpoint)
    if not nonblank(args.name) or not finite_number(args.timeout_seconds) or args.timeout_seconds <= 0:
        raise ContractError("A name and positive deadline are required")
    rows = read_rows(args.rows)
    request = build_request(rows, profile=args.profile, judge=args.judge, dataset_id=args.dataset_id)
    metric_contract = required_metrics(args.profile, json.loads(args.metric_contract.read_text(encoding="utf-8"))
                                       if args.metric_contract else None)
    plan = {"schema_version": "1.0", "project_endpoint": args.project_endpoint,
            "name": args.name, "profile": args.profile, "request": request,
            "rows_sha256": digest(rows), "metric_contract": metric_contract,
            "timeout_seconds": args.timeout_seconds, "output": str(args.output.resolve()),
            "runtime": runtime_provenance()}
    plan_sha256 = digest(plan)
    if not args.approve_plan:
        print(json.dumps({"would_submit": False, "rows": len(rows), "profile": args.profile,
                          "project_endpoint": args.project_endpoint, "judge": args.judge,
                          "metric_contract": metric_contract, "timeout_seconds": args.timeout_seconds,
                          "output": plan["output"], "runtime": plan["runtime"],
                          "plan_sha256": plan_sha256, "dataset_mode": "registered" if args.dataset_id else "inline"}))
        return 0
    if args.approve_plan != plan_sha256:
        raise ContractError("The approved request changed; review a new dry-run")
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    with DefaultAzureCredential() as credential:
        with AIProjectClient(endpoint=args.project_endpoint, credential=credential) as project:
            with project.get_openai_client() as client:
                result = run_cloud(client, rows=rows, plan=plan, output=args.output)
    print(json.dumps({key: result.get(key) for key in ("integrity", "quality_verdict", "eval_id", "run_id", "failed_stage")}))
    return 0 if result["integrity"] == "valid" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ContractError, OSError, ValueError) as error:
        print(f"Evaluation stopped: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)