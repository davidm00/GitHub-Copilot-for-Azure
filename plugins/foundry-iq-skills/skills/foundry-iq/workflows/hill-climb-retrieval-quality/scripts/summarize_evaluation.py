"""Revalidate saved cloud evidence and report usage without network or inference."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit

from evaluation_contract import (ContractError, build_request, capture_kb_row, digest,
                                 finite_number, read_rows, validate_rows)
from evaluate_cloud import (judge_usage, runtime_provenance, validate_endpoint,
                            verify_definition, verify_results, write_json)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def captured_efficiency(rows: list[dict[str, Any]], captures: list[dict[str, Any]], *,
                        profile: str, context_fields: list[str]) -> dict[str, Any]:
    if profile not in {"answer", "context", "reference"}:
        raise ContractError("Saved KB telemetry supports only answer, context and reference profiles")
    if (not context_fields or any(not isinstance(capture, dict) for capture in captures)
            or Counter(capture.get("id") for capture in captures) != Counter(row["id"] for row in rows)):
        raise ContractError("Require one same-call KB capture for every evaluated query and explicit context fields")
    by_id = {row["id"]: row for row in rows}
    durations = []
    activity_complete = True
    searches = 0
    stages: dict[tuple[str, str | None], list[dict[str, Any]]] = {}
    for capture in captures:
        row = by_id[capture["id"]]
        response = capture.get("response")
        if digest(capture_kb_row(row, response, context_fields=context_fields, answer=profile != "context")) != digest(row):
            raise ContractError("Saved KB capture does not reproduce the evaluated answer and context")
        elapsed = capture.get("elapsed_seconds")
        if finite_number(elapsed) and elapsed >= 0:
            durations.append(elapsed)
        activity = response.get("activity")
        if not isinstance(activity, list):
            activity_complete = False
            continue
        for item in activity:
            kind = item.get("type")
            if kind == "searchIndex":
                searches += 1
            elif isinstance(kind, str) and kind.startswith("model"):
                model = item.get("modelName")
                model = model if isinstance(model, str) and model.strip() else None
                stages.setdefault((kind, model), []).append(item)
    usage = []
    for (stage, model), items in stages.items():
        entry: dict[str, Any] = {"stage": stage, "model": model, "activity_entries": len(items)}
        for source, field in (("inputTokens", "input_tokens"), ("outputTokens", "output_tokens")):
            values = [item[source] for item in items if type(item.get(source)) is int and item[source] >= 0]
            entry[field] = sum(values) if len(values) == len(items) else None
            entry["known_" + field] = sum(values) if values else None
            entry["missing_" + field + "_entries"] = len(items) - len(values)
        usage.append(entry)
    return {
        "target_latency_seconds": ({"count": len(durations), "p50": percentile(durations, 0.5),
                                    "p95": percentile(durations, 0.95)} if len(durations) == len(rows) else None),
        "target_usage": {"scope": "exposed_model_activity_only", "activity_coverage_complete": activity_complete,
                         "by_stage_and_model": usage} if usage else None,
        "search_count": searches if activity_complete else None,
        "target_measurement_limitation": "Only these evaluated captures; excludes other probes, failed attempts, hidden activity and billing. Attach the full attempt ledger separately.",
    }


def saved_report(directory: Path, *, rows: list[dict[str, Any]] | None = None,
                 captures: list[dict[str, Any]] | None = None,
                 context_fields: list[str] | None = None) -> dict[str, Any]:
    artifacts = {}

    def load(name: str):
        content = (directory / name).read_bytes()
        artifacts[name] = hashlib.sha256(content).hexdigest()
        text = content.decode("utf-8-sig")
        return ([json.loads(line) for line in text.splitlines() if line.strip()]
                if name.endswith(".jsonl") else json.loads(text))

    plan, receipt = load("plan.json"), load("result.json")
    evaluation, run, items = load("evaluation.json"), load("run.json"), load("output-items.jsonl")
    request, profile = plan["request"], plan["profile"]
    validate_endpoint(plan["project_endpoint"])
    source = request["data_source"]["source"]
    if rows is None:
        if source.get("type") != "file_content":
            raise ContractError("Registered-dataset replay requires the original captured --rows file")
        rows = [entry["item"] for entry in source["content"]]
    validate_rows(rows, profile)
    parameters = request["testing_criteria"][0].get("initialization_parameters", {})
    judge = parameters.get("deployment_name", parameters.get("model"))
    expected = build_request(rows, profile=profile, judge=judge,
                             dataset_id=source.get("id") if source.get("type") == "file_id" else None)
    if "model" in parameters and "deployment_name" not in parameters:
        # Preserve read-only inspection of historical requests without resubmitting them.
        for criterion in expected["testing_criteria"]:
            initialization = criterion["initialization_parameters"]
            if "deployment_name" in initialization:
                initialization["model"] = initialization.pop("deployment_name")
    for observed, criterion in zip(request["testing_criteria"], expected["testing_criteria"]):
        if (observed.get("name") == criterion["name"] == "retrieval"
                and "response" not in observed.get("data_mapping", {})):
            criterion["data_mapping"].pop("response", None)
            if "response" not in request["data_source_config"]["item_schema"]["properties"]:
                expected["data_source_config"]["item_schema"]["properties"].pop("response", None)
    if (digest(request) != digest(expected) or receipt.get("plan_sha256") != digest(plan)
            or digest(rows) != plan.get("rows_sha256") or digest(rows) != receipt.get("dataset_sha256")
            or receipt.get("project_endpoint") != plan["project_endpoint"]
            or receipt.get("profile") != profile or receipt.get("expected_rows") != len(rows)):
        raise ContractError("Saved request, dataset or receipt does not match the frozen plan")
    verify_definition(request, evaluation)
    report_url = urlsplit(run.get("report_url") or "")
    if (evaluation.get("id") != receipt.get("eval_id") or run.get("eval_id") != receipt.get("eval_id")
            or run.get("id") != receipt.get("run_id") or run.get("status") != "completed"
            or run.get("error") is not None or digest(run.get("data_source")) != digest(request["data_source"])
            or report_url.scheme != "https" or report_url.hostname != "ai.azure.com"
            or report_url.username or report_url.password or report_url.port not in (None, 443)):
        raise ContractError("Saved cloud run identity, source, status or report URL is invalid")
    verified = verify_results(rows, items, profile=profile, eval_id=receipt["eval_id"],
                              run_id=receipt["run_id"], metric_contract=plan.get("metric_contract"))
    expected_counts = {"total": len(rows), "failed": verified["failed_quality_rows"],
                       "passed": len(rows) - verified["failed_quality_rows"], "errored": 0}
    counts = run.get("result_counts")
    if not isinstance(counts, dict) or any(type(counts.get(key)) is not int or counts[key] != value
                                          for key, value in expected_counts.items()):
        raise ContractError("Saved service counts disagree with retained row results")
    if receipt.get("integrity") == "valid":
        original_rows = receipt.get("rows")
        if (not isinstance(original_rows, list)
                or digest(receipt.get("metrics")) != digest(verified["metrics"])
                or Counter(digest(row) for row in original_rows) != Counter(digest(row) for row in verified["rows"])):
            raise ContractError("Saved scores or reasons disagree with the original valid receipt")
    report = {
        **verified, "schema_version": "1.0", "execution_mode": "saved_evaluation_report",
        "created_at": datetime.now(timezone.utc).isoformat(), "new_inference_calls": 0,
        "source_receipt_integrity": receipt.get("integrity"), "saved_evidence_integrity": "valid",
        "integrity": "valid" if receipt.get("integrity") == "valid" else "invalid",
        "original_verdict_limitation": "Revalidation never promotes an invalid original receipt or proves workload quality",
        "plan_sha256": digest(plan), "dataset_sha256": digest(rows), "profile": profile,
        "project_endpoint": plan["project_endpoint"], "service_status": run["status"],
        "eval_id": run["eval_id"], "run_id": run["id"], "report_url": run["report_url"],
        "artifact_sha256": artifacts,
        "summarizer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reporter_runtime": runtime_provenance(),
        "judge_usage": judge_usage(items, profile), "total_cost": None,
        "target_latency_seconds": None, "target_usage": None, "search_count": None,
        "evaluation_wall_seconds": receipt.get("evaluation_wall_seconds"),
        "target_verification": "unverified",
        "measurement_limitations": {
            "target_latency_seconds": "Incomplete or absent capture timing; cloud wall time is not target latency",
            "target_usage": "No same-call KB activity supplied; do not retrieve again to fill it",
            "search_count": "No same-call Search activity supplied",
            "total_cost": "No complete attributable Search billing or verified component prices; no dollar estimate",
            "target_verification": "Saved output inspection cannot prove the current target configuration is unchanged",
        },
    }
    if captures is not None:
        report.update(captured_efficiency(rows, captures, profile=profile, context_fields=context_fields or []))
        report["capture_sha256"] = digest(captures)
        report["capture_context_fields"] = context_fields
        for field in ("target_latency_seconds", "target_usage", "search_count"):
            if report[field] is not None:
                report["measurement_limitations"][field] = report["target_measurement_limitation"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--run-directory", required=True, type=Path)
    parser.add_argument("--rows", type=Path, help="Original captured rows; required for registered datasets")
    parser.add_argument("--capture-ledger", type=Path, help="Saved same-call KB responses and elapsed_seconds by query id")
    parser.add_argument("--context-field", action="append", help="Actual sourceData field used during capture; repeat as needed")
    parser.add_argument("--output", required=True, type=Path, help="New private JSON file outside the original run directory")
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.run_directory.resolve()):
        raise ContractError("Write derived reports outside the immutable original run directory")
    if bool(args.capture_ledger) != bool(args.context_field):
        raise ContractError("Supply both a saved KB capture ledger and its original context field mapping")
    report = saved_report(args.run_directory, rows=read_rows(args.rows) if args.rows else None,
                          captures=read_rows(args.capture_ledger) if args.capture_ledger else None,
                          context_fields=args.context_field)
    write_json(args.output, report)
    print(json.dumps({key: report[key] for key in ("integrity", "saved_evidence_integrity", "eval_id", "run_id", "new_inference_calls")}))
    return 0 if report["integrity"] == "valid" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ContractError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Saved report stopped: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)