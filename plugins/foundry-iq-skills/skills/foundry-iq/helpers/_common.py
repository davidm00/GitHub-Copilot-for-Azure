from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from http.client import HTTPException
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


SEARCH_AUDIENCE = "https://search.azure.com"
MANAGEMENT_AUDIENCE = "https://management.azure.com"
SEARCH_HOST = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?\.search\.windows\.net$"
)
SECRET_FIELDS = {
    "accesskey",
    "accesstoken",
    "accountkey",
    "apikey",
    "applicationsecret",
    "authorization",
    "clientsecret",
    "credential",
    "connectionsecret",
    "key",
    "password",
    "privatekey",
    "refreshtoken",
    "sas",
    "sastoken",
    "secret",
    "sharedaccesskey",
    "storageaccountkey",
    "token",
}
RESOURCE_ID_CONNECTION = re.compile(r"^ResourceId=/[^;\r\n]+;?$")


def normalize_azure_location(value: Any) -> str | None:
    """Normalize ASCII case/whitespace only; this does not validate region availability."""
    if not isinstance(value, str) or len(value) > 128 or not value.isascii():
        return None
    compact = re.sub(r"\s+", "", value, flags=re.ASCII).lower()
    return compact if re.fullmatch(r"[a-z][a-z0-9]{1,40}", compact) else None


def _normalize_response_headers(headers: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for name, value in headers.items():
        key = name.lower()
        if key in {"x-ms-request-id", "request-id"} and normalized.get(key):
            continue
        normalized[key] = value
    return normalized


def _request_id(headers: Mapping[str, str]) -> str | None:
    normalized = _normalize_response_headers(headers)
    return normalized.get("x-ms-request-id") or normalized.get("request-id") or None


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: Any
    headers: dict[str, str]

    @property
    def request_id(self) -> str | None:
        return _request_id(self.headers)


class HelperFailure(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        blocked_at: str,
        writes: list[dict[str, Any]] | None = None,
        resources_remaining: list[dict[str, Any]] | None = None,
        request_id: str | None = None,
        status: int | None = None,
        partial: bool = False,
        warnings: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.blocked_at = blocked_at
        self.writes = writes or []
        self.resources_remaining = resources_remaining or []
        self.request_id = request_id
        self.http_status = status
        self.partial = partial
        self.warnings = warnings or []


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_bytes(value)).hexdigest()}"


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def load_approved_input(path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HelperFailure(
            "input-unreadable",
            "Input file cannot be read.",
            blocked_at="input-resolution",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HelperFailure(
            "input-invalid-json",
            f"Input file is not valid JSON: {exc}",
            blocked_at="input-resolution",
        ) from exc
    if not isinstance(document, dict) or document.get("schema_version") != "1.0":
        raise HelperFailure(
            "input-schema-invalid",
            "Input must be an object with schema_version 1.0.",
            blocked_at="input-resolution",
        )
    reject_secrets(document)
    require_allowed_fields(
        document,
        {"schema_version", "plan", "approval"},
        label="input envelope",
    )
    plan = document.get("plan")
    approval = document.get("approval")
    if not isinstance(plan, dict) or not isinstance(approval, dict):
        raise HelperFailure(
            "input-schema-invalid",
            "Input must contain plan and approval objects.",
            blocked_at="input-resolution",
        )
    require_allowed_fields(
        approval,
        {"confirmed", "fingerprint"},
        label="approval",
    )
    computed = digest(plan)
    if approval.get("confirmed") is not True:
        raise HelperFailure(
            "approval-missing",
            "The exact plan has not been explicitly approved.",
            blocked_at="confirmation",
        )
    if approval.get("fingerprint") != computed:
        raise HelperFailure(
            "approval-mismatch",
            "The approved fingerprint does not match the canonical plan.",
            blocked_at="confirmation",
        )
    return document, plan, computed


def reject_secrets(value: Any, *, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            child_path = f"{path}/{key}"
            if normalized in SECRET_FIELDS and child not in (None, "", []):
                raise HelperFailure(
                    "secret-input-forbidden",
                    f"Secret-bearing field is forbidden at {child_path}.",
                    blocked_at="input-resolution",
                )
            if normalized == "connectionstring" and child not in (None, ""):
                if (
                    not isinstance(child, str)
                    or RESOURCE_ID_CONNECTION.fullmatch(child) is None
                ):
                    raise HelperFailure(
                        "secret-input-forbidden",
                        "Only one ResourceId storage connectionString component is allowed.",
                        blocked_at="input-resolution",
                    )
            reject_secrets(child, path=child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secrets(child, path=f"{path}/{index}")


def require_allowed_fields(
    value: dict[str, Any],
    allowed: set[str],
    *,
    label: str,
) -> None:
    if set(value) - allowed:
        raise HelperFailure(
            "input-schema-invalid",
            f"{label} contains unsupported fields.",
            blocked_at="input-resolution",
        )


def is_ambiguous_mutation_failure(failure: HelperFailure) -> bool:
    return (
        failure.partial
        or failure.code == "azure-response-ambiguous"
        or failure.http_status in {408, 429}
        or (
            isinstance(failure.http_status, int)
            and failure.http_status >= 500
        )
    )


def is_ambiguous_status(status: int) -> bool:
    return status in {408, 429} or status >= 500


def sdk_error_status(error: Exception) -> int | None:
    for source in (error, getattr(error, "response", None)):
        status = getattr(source, "status_code", None)
        if type(status) is int and 100 <= status <= 599:
            return status
    return None


def sdk_error_metadata(error: Exception, fallback_code: str | None = None) -> dict[str, Any]:
    """Read only bounded identifier fields, never exception text or response bodies."""
    def identifier(value: Any) -> str | None:
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value):
            return value
        return None

    response = getattr(error, "response", None)
    raw_headers = getattr(response, "headers", None)
    headers = {}
    if isinstance(raw_headers, Mapping):
        headers = _normalize_response_headers({
            key: identifier(value)
            for key, value in raw_headers.items()
            if isinstance(key, str) and key.lower() in {"x-ms-request-id", "request-id", "x-ms-error-code"}
        })
    result = {"status": sdk_error_status(error), "request_id": _request_id(headers)}
    if fallback_code is not None:
        detail = getattr(error, "error", None)
        code = detail.get("code") if isinstance(detail, Mapping) else getattr(detail, "code", None)
        result["code"] = (
            identifier(code) or identifier(getattr(error, "code", None))
            or headers.get("x-ms-error-code") or fallback_code
        )
    return result


def is_ambiguous_sdk_error(error: Exception) -> bool:
    status = sdk_error_status(error)
    return status is None or is_ambiguous_status(status)


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in SECRET_FIELDS or normalized == "connectionstring":
                result[str(key)] = "[REDACTED]"
            else:
                result[str(key)] = redact_sensitive(child)
        return result
    if isinstance(value, list):
        return [redact_sensitive(child) for child in value]
    return value


def validate_search_endpoint(endpoint: Any) -> str:
    if not isinstance(endpoint, str):
        raise HelperFailure(
            "endpoint-invalid",
            "Search endpoint must be a string.",
            blocked_at="input-resolution",
        )
    try:
        endpoint.encode("utf-8")
        parsed = urlsplit(endpoint)
        port = parsed.port
    except (ValueError, UnicodeEncodeError) as exc:
        raise HelperFailure(
            "endpoint-invalid",
            "Search endpoint must be a valid UTF-8 HTTPS service root.",
            blocked_at="input-resolution",
        ) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or SEARCH_HOST.fullmatch(parsed.hostname) is None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
        or port not in {None, 443}
    ):
        raise HelperFailure(
            "endpoint-invalid",
            "Search endpoint must be an HTTPS search.windows.net service root.",
            blocked_at="input-resolution",
        )
    return endpoint.rstrip("/")


def odata_name(name: Any) -> str:
    if not isinstance(name, str) or not name or len(name) > 128:
        raise HelperFailure(
            "name-invalid",
            "Resource name must be a non-empty string no longer than 128 characters.",
            blocked_at="input-resolution",
        )
    try:
        return quote(name.replace("'", "''"), safe="")
    except UnicodeEncodeError as exc:
        raise HelperFailure(
            "name-invalid",
            "Resource name must be valid UTF-8 text.",
            blocked_at="input-resolution",
        ) from exc


def azure_cli_token(resource: str) -> str:
    try:
        executable = shutil.which("az")
        if executable is None:
            raise FileNotFoundError("Azure CLI executable was not found on PATH.")
        completed = subprocess.run(
            [
                executable,
                "account",
                "get-access-token",
                "--resource",
                resource,
                "--query",
                "accessToken",
                "--output",
                "tsv",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise HelperFailure(
            "azure-cli-unavailable",
            "Azure CLI is required for keyless authentication.",
            blocked_at="execution",
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise HelperFailure(
            "azure-authentication-failed",
            "Azure CLI could not acquire the required access token.",
            blocked_at="execution",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise HelperFailure(
            "azure-authentication-timeout",
            "Azure CLI did not return an access token within 60 seconds.",
            blocked_at="execution",
        ) from exc
    token = completed.stdout.strip()
    if not token:
        raise HelperFailure(
            "azure-authentication-failed",
            "Azure CLI returned an empty access token.",
            blocked_at="execution",
        )
    return token


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def _read_response_with_deadline(
    response: Any, deadline: float, max_bytes: int, *, method: str
) -> bytes:
    def timed_out() -> HelperFailure:
        return HelperFailure(
            "response-deadline-exceeded",
            "HTTP response body exceeded its monotonic deadline.",
            blocked_at="verification",
            request_id=_request_id(response.headers),
            status=response.status,
            partial=method not in {"GET", "HEAD"},
        )

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise timed_out()
    connection = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
    if not isinstance(connection, socket.socket):
        raise HelperFailure(
            "response-deadline-unsupported",
            "Deadline reads require an interruptible urllib HTTP socket.",
            blocked_at="verification",
            request_id=_request_id(response.headers),
            status=response.status,
            partial=method not in {"GET", "HEAD"},
        )
    expired = threading.Event()

    def interrupt() -> None:
        expired.set()
        # BufferedReader.close can wait on the active read lock; interrupt its socket instead.
        with suppress(OSError):
            connection.shutdown(socket.SHUT_RDWR)
        with suppress(OSError):
            connection.close()

    watchdog = threading.Timer(max(0, deadline - time.monotonic()), interrupt)
    watchdog.start()
    try:
        if expired.is_set() or time.monotonic() >= deadline:
            raise timed_out()
        try:
            payload = response.read(max_bytes + 1)
        except (OSError, HTTPException, ValueError) as exc:
            if expired.is_set() or time.monotonic() >= deadline:
                raise timed_out() from exc
            raise HelperFailure(
                "response-read-failed", "HTTP response body could not be read.",
                blocked_at="verification",
                request_id=_request_id(response.headers),
                status=response.status,
                partial=method not in {"GET", "HEAD"},
            ) from exc
        if expired.is_set() or time.monotonic() >= deadline:
            raise timed_out()
        return payload
    finally:
        watchdog.cancel()
        watchdog.join()


def http_request(
    method: str,
    url: str,
    token: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 180,
    raw_response: bool = False,
    max_response_bytes: int | None = None,
    follow_redirects: bool = True,
    response_deadline: float | None = None,
) -> HttpResult:
    if response_deadline is not None:
        if (
            not isinstance(response_deadline, (int, float))
            or not math.isfinite(response_deadline)
            or response_deadline - time.monotonic() > threading.TIMEOUT_MAX
        ):
            raise HelperFailure(
                "response-deadline-invalid", "Response deadline must be a supported finite monotonic time.",
                blocked_at="input-resolution",
            )
        if max_response_bytes is None:
            max_response_bytes = 1024 * 1024
        if not isinstance(max_response_bytes, int) or max_response_bytes < 0:
            raise HelperFailure(
                "response-limit-invalid", "Response byte limit must be a nonnegative integer.",
                blocked_at="input-resolution",
            )
        if response_deadline <= time.monotonic():
            raise HelperFailure(
                "response-deadline-exceeded", "HTTP deadline elapsed before the request.",
                blocked_at="verification",
            )
    request_headers = {
        "Accept": "application/json;odata.metadata=minimal",
        "Authorization": f"Bearer {token}",
        "x-ms-client-request-id": str(uuid.uuid4()),
    }
    request_headers.update(headers or {})
    request = Request(url=url, data=body, headers=request_headers, method=method)
    try:
        open_request = urlopen if follow_redirects else build_opener(_NoRedirect).open
        with open_request(request, timeout=timeout) as response:
            if response_deadline is not None:
                payload = _read_response_with_deadline(
                    response, response_deadline, max_response_bytes, method=method
                )
            else:
                payload = (
                    response.read(max_response_bytes + 1)
                    if max_response_bytes is not None
                    else response.read()
                )
            response_headers = _normalize_response_headers(response.headers)
            if max_response_bytes is not None and len(payload) > max_response_bytes:
                raise HelperFailure(
                    "response-too-large",
                    "Azure response exceeded the bounded read limit.",
                    blocked_at="verification",
                    request_id=_request_id(response_headers),
                    status=response.status,
                    partial=method not in {"GET", "HEAD"},
                )
            if raw_response:
                parsed: Any = payload
            elif not payload:
                parsed = None
            else:
                try:
                    parsed = json.loads(payload.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise HelperFailure(
                        "response-invalid-json",
                        "Azure returned a non-JSON response where JSON was required.",
                        blocked_at="verification",
                        request_id=_request_id(response_headers),
                        status=response.status,
                        partial=method not in {"GET", "HEAD"},
                    ) from exc
            return HttpResult(response.status, parsed, response_headers)
    except HTTPError as exc:
        response_headers = _normalize_response_headers(exc.headers)
        status = int(exc.code)
        if response_deadline is not None:
            exc.close()
        ambiguous = method not in {"GET", "HEAD"} and is_ambiguous_status(status)
        raise HelperFailure(
            "azure-http-error",
            f"Azure request failed with HTTP {status}.",
            blocked_at="execution",
            request_id=_request_id(response_headers),
            status=status,
            partial=ambiguous,
        ) from exc
    except (URLError, TimeoutError) as exc:
        raise HelperFailure(
            "azure-response-ambiguous",
            "Azure request did not return an authoritative response.",
            blocked_at="verification",
            partial=method not in {"GET", "HEAD"},
        ) from exc


def blocked_result(
    failure: HelperFailure,
    *,
    outcome: str,
    fingerprint: str | None,
    owner: Any = None,
) -> dict[str, Any]:
    if failure.partial or failure.writes:
        return {
            "status": "partial",
            "outcome": outcome,
            "approved_plan": {
                "fingerprint": fingerprint,
                "confirmed": fingerprint is not None,
            },
            "first_failure": {
                "code": failure.code,
                "operation": failure.blocked_at,
                "status": failure.http_status,
                "message": failure.message,
                "request_id": failure.request_id,
            },
            "completed_writes": failure.writes,
            "failed_or_unverified_postconditions": [failure.code],
            "resources_remaining": {
                "run_owned": failure.resources_remaining,
                "reused": [],
            },
            "rollback": {"possible": False, "exact_plan": []},
            "cleanup": {"status": "separate-plan-and-approval-required"},
            "owner": owner,
            "warnings": failure.warnings,
        }
    result = {
        "status": "blocked",
        "outcome": outcome,
        "blocked_at": failure.blocked_at,
        "first_blocker": {
            "code": failure.code,
            "message": failure.message,
            "status": failure.http_status,
            "request_id": failure.request_id,
        },
        "missing_or_conflicting_input": failure.code,
        "read_only_evidence": [],
        "writes_performed": [],
        "safe_next_decision": "Resolve the first blocker, rebuild the plan, and obtain new approval.",
        "ownership": {"run_owned": [], "reused_not_owned": []},
        "cleanup": "not applicable",
    }
    if fingerprint is not None:
        result["approved_plan"] = {
            "fingerprint": fingerprint,
            "confirmed": True,
        }
    if failure.warnings:
        result["warnings"] = failure.warnings
    return result


def emit_result(
    result: dict[str, Any], *, stream: Any = None, preserve_unapproved_input: bool = False
) -> None:
    if stream is None:
        stream = sys.stdout
    safe = redact_sensitive(result)
    if preserve_unapproved_input:
        document = result.get("execution_input")
        if (
            result.get("status") != "planned" or not isinstance(document, dict)
            or document.get("schema_version") != "1.0" or not isinstance(document.get("plan"), dict)
            or not isinstance(document.get("approval"), dict)
            or document["approval"].get("confirmed") is not False
            or document.get("approval") != {"confirmed": False, "fingerprint": digest(document["plan"])}
        ):
            raise HelperFailure(
                "planning-output-invalid", "Only an exact unapproved execution input can retain ResourceId bindings.",
                blocked_at="verification",
            )
        reject_secrets(document)
        require_allowed_fields(document, {"schema_version", "plan", "approval"}, label="planning envelope")
        safe["execution_input"] = document
    stream.write(
        json.dumps(
            safe,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


TokenProvider = Callable[[str], str]
Transport = Callable[..., HttpResult]
