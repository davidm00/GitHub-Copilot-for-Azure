"""Pure data contracts for the retrieval-quality workflow; no Azure calls."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


PROFILES = {
    "answer": ("groundedness", "relevance", "retrieval"),
    "context": ("retrieval",),
    "reference": ("groundedness", "relevance", "retrieval", "response_completeness"),
    "ranking": ("document_retrieval",),
}
INPUTS = {
    "groundedness": ("query", "response", "context"),
    "relevance": ("query", "response"),
    "retrieval": ("query", "context"),
    "response_completeness": ("response", "ground_truth"),
    "document_retrieval": ("retrieval_ground_truth", "retrieved_documents"),
}


class ContractError(ValueError):
    pass


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def finite_number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def reject_credentials(value: Any) -> None:
    forbidden = {"api_key", "apikey", "authorization", "access_token", "refresh_token",
                 "auth_token", "end_user_token", "client_secret", "password", "connection_string",
                 "x_ms_query_source_authorization", "sas_token", "sig"}
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or key.lower().replace("-", "_") in forbidden:
                raise ContractError("Remove credential fields before admission or upload")
            reject_credentials(child)
    elif isinstance(value, list):
        for child in value:
            reject_credentials(child)


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        if path.suffix.lower() == ".csv":
            return list(csv.DictReader(stream))
        if path.suffix.lower() == ".json":
            rows = json.load(stream)
        elif path.suffix.lower() == ".jsonl":
            rows = [json.loads(line) for line in stream if line.strip()]
        else:
            raise ContractError("Use JSON, JSONL or CSV with an explicit field mapping")
    if not isinstance(rows, list):
        raise ContractError("The dataset must be an array of rows")
    return rows


def normalize_queries(rows: list[dict[str, Any]], *, query_field: str = "query",
                      id_field: str = "id", generated: bool = False) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise ContractError("Review a nonempty evaluation set before inference")
    normalized = []
    identifiers: set[str] = set()
    for original in rows:
        if not isinstance(original, dict) or not nonblank(original.get(query_field)):
            raise ContractError("Every row requires a nonblank query; do not drop failed rows")
        reject_credentials(original)
        row = copy.deepcopy(original)
        row["query"] = original[query_field]
        identifier = original.get(id_field)
        if identifier is None:
            identifier = "query-" + digest(original)
        if not nonblank(identifier) or identifier in identifiers:
            raise ContractError("Query IDs must be nonblank and unique")
        identifiers.add(identifier)
        row["id"] = identifier
        if generated:
            if "ground_truth" in row:
                row["proposed_answer"] = row.pop("ground_truth")
            row.pop("ground_truth_provenance", None)
            row["origin"] = "generated-unreviewed"
        digest(row)
        normalized.append(row)
    return normalized


def validate_rows(rows: list[dict[str, Any]], profile: str, *, agent: bool = False) -> None:
    if profile not in PROFILES:
        raise ContractError("Unknown evaluation profile")
    if agent and profile in {"context", "ranking"}:
        raise ContractError("Use captured evidence for context-only or ranked-document scoring")
    normalized = normalize_queries(rows)
    if normalized != rows:
        raise ContractError("Assign stable query IDs before freezing the run")
    fields = {field for name in PROFILES[profile] for field in INPUTS[name]}
    if agent:
        fields -= {"response", "context"}
    for row in rows:
        if row.get("origin") == "generated-unreviewed":
            raise ContractError("Review generated questions before evaluation")
        for field in fields - {"retrieval_ground_truth", "retrieved_documents"}:
            if not nonblank(row.get(field)):
                raise ContractError(f"Missing required {field}; retain the failed row")
        if profile == "reference":
            provenance = row.get("ground_truth_provenance")
            if (not isinstance(provenance, dict)
                    or not nonblank(provenance.get("source"))
                    or not nonblank(provenance.get("verified_by"))):
                raise ContractError("Reference scoring requires independently verified answers")
        if profile == "ranking":
            for field, score_field in (("retrieval_ground_truth", "query_relevance_label"),
                                       ("retrieved_documents", "relevance_score")):
                documents = row.get(field)
                if not isinstance(documents, list) or (field == "retrieval_ground_truth" and not documents):
                    raise ContractError("Ranking requires reviewed qrels and actual retrieved documents")
                identifiers = []
                for document in documents:
                    if (not isinstance(document, dict) or not nonblank(document.get("document_id"))
                            or not finite_number(document.get(score_field))):
                        raise ContractError("Invalid canonical document ID or ranking value")
                    if field == "retrieval_ground_truth" and not 0 <= document[score_field] <= 4:
                        raise ContractError("This profile uses the reviewed 0-4 qrel scale")
                    identifiers.append(document["document_id"])
                if len(set(identifiers)) != len(identifiers):
                    raise ContractError("Resolve duplicate chunks to canonical documents before scoring")


def capture_kb_row(row: dict[str, Any], result: dict[str, Any], *,
                   context_fields: list[str], answer: bool = True) -> dict[str, Any]:
    if (not isinstance(result, dict) or result.get("error") is not None
            or not context_fields or not all(nonblank(field) for field in context_fields)):
        raise ContractError("Require a successful retrieve result and explicit source fields")
    activity = result.get("activity", [])
    if (not isinstance(activity, list)
            or any(not isinstance(item, dict) or item.get("error") is not None for item in activity)):
        raise ContractError("Partial retrieval is a failure, not valid context")
    passages = []
    references = result.get("references", [])
    if not isinstance(references, list):
        raise ContractError("Malformed retrieval references")
    for reference in references:
        source = reference.get("sourceData") if isinstance(reference, dict) else None
        if not isinstance(source, dict):
            raise ContractError("A retrieved reference has no source data")
        values = [source.get(field) for field in context_fields]
        usable = [value.strip() for value in values if nonblank(value)]
        if not usable:
            raise ContractError("A retrieved reference has no configured context field")
        passages.extend(usable)
    captured = copy.deepcopy(row)
    captured["context"] = "\n\n".join(passages)
    if not captured["context"]:
        raise ContractError("Missing retrieved context; retain the failure without a second retrieval")
    if answer:
        response = result.get("response", [])
        if not isinstance(response, list):
            raise ContractError("Malformed response")
        texts = []
        for message in response:
            content = message.get("content", []) if isinstance(message, dict) else []
            if not isinstance(content, list):
                raise ContractError("Malformed response content")
            texts.extend(part["text"] for part in content if isinstance(part, dict)
                         and part.get("type") == "text" and nonblank(part.get("text")))
        captured["response"] = "\n".join(texts).strip()
        if not captured["response"]:
            raise ContractError("Missing answer; do not fabricate synthesis")
    return captured


def build_request(rows: list[dict[str, Any]], *, profile: str = "answer",
                  judge: str | None = None, agent: dict[str, str] | None = None,
                  dataset_id: str | None = None) -> dict[str, Any]:
    validate_rows(rows, profile, agent=agent is not None)
    if profile != "ranking" and not nonblank(judge):
        raise ContractError("Resolve the approved cloud judge deployment first")
    if agent is not None and (set(agent) != {"name", "version"}
                              or not all(nonblank(value) for value in agent.values())
                              or agent["version"].strip().lower() == "latest"):
        raise ContractError("Freeze an existing agent name and exact version")
    if dataset_id is not None and not nonblank(dataset_id):
        raise ContractError("Use a verified dataset ID, not a local path")
    retrieval_response = "retrieval" in PROFILES[profile] and (
        agent is not None or any("response" in row for row in rows)
    )
    criteria = []
    for name in PROFILES[profile]:
        mapping = {field: "{{item." + field + "}}" for field in INPUTS[name]}
        if name == "retrieval" and retrieval_response:
            mapping["response"] = "{{item.response}}"
        if agent is not None:
            if "response" in mapping:
                mapping["response"] = "{{sample.output_text}}"
            if "context" in mapping:
                mapping["context"] = "{{sample.tool_calls}}"
        criteria.append({
            "type": "azure_ai_evaluator", "name": name,
            "evaluator_name": "builtin." + name,
            "initialization_parameters": ({"ground_truth_label_min": 0, "ground_truth_label_max": 4}
                                          if name == "document_retrieval" else {"deployment_name": judge}),
            "data_mapping": mapping,
        })
    fields = {"id", "query"} | {field for name in PROFILES[profile] for field in INPUTS[name]}
    if agent is not None:
        fields -= {"response", "context"}
    properties = {field: {"type": "string"} for field in sorted(fields)}
    if retrieval_response and agent is None:
        properties["response"] = {"type": "string"}
    if profile == "ranking":
        for field in ("retrieval_ground_truth", "retrieved_documents"):
            properties[field] = {"type": "array", "items": {"type": "object"}}
    schema: dict[str, Any] = {"type": "custom", "item_schema": {
        "type": "object", "properties": properties, "required": sorted(fields)}}
    source = ({"type": "file_id", "id": dataset_id} if dataset_id else {
        "type": "file_content", "content": [{"item": copy.deepcopy(row)} for row in rows]})
    data_source: dict[str, Any] = {"type": "jsonl", "source": source}
    if agent is not None:
        schema["include_sample_schema"] = True
        data_source = {
            "type": "azure_ai_target_completions", "source": source,
            "input_messages": {"type": "template", "template": [{
                "type": "message", "role": "user",
                "content": {"type": "input_text", "text": "{{item.query}}"}}]},
            "target": {"type": "azure_ai_agent", **agent},
        }
    return {"data_source_config": schema, "testing_criteria": criteria, "data_source": data_source}