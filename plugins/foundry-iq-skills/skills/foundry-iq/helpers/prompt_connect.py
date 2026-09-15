from __future__ import annotations

import argparse
import json
import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

try:
    from ._common import (
        MANAGEMENT_AUDIENCE,
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
        is_ambiguous_sdk_error,
        load_approved_input,
        reject_secrets,
        require_allowed_fields,
        sdk_error_metadata,
    )
except ImportError:
    from _common import (  # type: ignore[no-redef]
        MANAGEMENT_AUDIENCE,
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
        is_ambiguous_sdk_error,
        load_approved_input,
        reject_secrets,
        require_allowed_fields,
        sdk_error_metadata,
    )


ARM_API_VERSION = "2025-10-01-preview"
SDK_MAJOR = "2"
GROUNDING = (
    "For every user question, call knowledge_base_retrieve before answering, "
    "including questions that seem unrelated to the knowledge base. "
    "Answer only from evidence returned for that question and cite the original "
    "sources. Do not answer from general knowledge or assume an answer without "
    "retrieval. If the retrieved evidence does not support an answer, reply "
    "exactly: I don't know. Do not add citations to an unsupported answer. "
    "If retrieval fails, report the failure instead of treating it as no evidence "
    "or answering from general knowledge."
)
PROJECT_ID = re.compile(
    r"^/subscriptions/[^/]+/resourceGroups/[^/]+/providers/"
    r"Microsoft\.CognitiveServices/accounts/(?P<account>[^/]+)/projects/"
    r"(?P<project>[^/]+)$",
    re.IGNORECASE,
)
PROJECT_PATH = re.compile(r"^/api/projects/(?P<project>[^/]+)/?$")
SEARCH_HOST = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?\.search\.windows\.net$"
)
KB_MCP_PATH = re.compile(r"^/knowledgebases/[^/]+/mcp$")
SHA256 = re.compile(r"^sha256:[a-f0-9]{64}$")
PLAN_FIELDS = {
    "operation",
    "outcome",
    "sdk_major",
    "project_resource_id",
    "project_endpoint",
    "connection",
    "agent",
    "rbac_verified",
    "allowed_tools",
    "require_approval",
    "permission_forwarding",
    "grounding_instructions",
    "network",
    "owner",
    "cleanup_approved",
}


def _project_endpoint(value: Any) -> str:
    if not isinstance(value, str):
        raise HelperFailure(
            "project-endpoint-invalid",
            "Project endpoint must be a string.",
            blocked_at="input-resolution",
        )
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".services.ai.azure.com")
        or PROJECT_PATH.fullmatch(parsed.path) is None
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise HelperFailure(
            "project-endpoint-invalid",
            "Project endpoint must be an HTTPS services.ai.azure.com project URL.",
            blocked_at="input-resolution",
        )
    return value.rstrip("/")


def _project_identity(plan: dict[str, Any]) -> tuple[str, str]:
    project_id = plan.get("project_resource_id")
    match = PROJECT_ID.fullmatch(project_id) if isinstance(project_id, str) else None
    if match is None:
        raise HelperFailure(
            "project-resource-id-invalid",
            "project_resource_id must identify one Microsoft Foundry project.",
            blocked_at="input-resolution",
        )
    endpoint = _project_endpoint(plan.get("project_endpoint"))
    parsed = urlsplit(endpoint)
    endpoint_account = parsed.hostname.removesuffix(".services.ai.azure.com")
    endpoint_match = PROJECT_PATH.fullmatch(parsed.path)
    if (
        endpoint_match is None
        or endpoint_account.casefold() != match.group("account").casefold()
        or unquote(endpoint_match.group("project")).casefold()
        != match.group("project").casefold()
    ):
        raise HelperFailure(
            "project-identity-mismatch",
            "project_endpoint and project_resource_id must identify the same Foundry project.",
            blocked_at="reconciliation",
        )
    return project_id, endpoint


def _connection_url(plan: dict[str, Any]) -> str:
    project_id = plan.get("project_resource_id")
    if not isinstance(project_id, str) or PROJECT_ID.fullmatch(project_id) is None:
        raise HelperFailure(
            "project-resource-id-invalid",
            "project_resource_id must identify one Microsoft Foundry project.",
            blocked_at="input-resolution",
        )
    connection = plan.get("connection")
    if not isinstance(connection, dict):
        raise HelperFailure(
            "connection-invalid",
            "connection must be an object.",
            blocked_at="input-resolution",
        )
    name = connection.get("name")
    if not isinstance(name, str) or not name:
        raise HelperFailure(
            "connection-invalid",
            "connection.name is required.",
            blocked_at="input-resolution",
        )
    return (
        "https://management.azure.com"
        f"{project_id}/connections/{quote(name, safe='')}?"
        + urlencode({"api-version": ARM_API_VERSION})
    )


def connection_definition(plan: dict[str, Any]) -> dict[str, Any]:
    connection = plan["connection"]
    return {
        "name": connection["name"],
        "type": "Microsoft.CognitiveServices/accounts/projects/connections",
        "properties": {
            "authType": "ProjectManagedIdentity",
            "category": "RemoteTool",
            "target": connection["target"],
            "isSharedToAll": connection.get("is_shared_to_all", True),
            "audience": "https://search.azure.com/",
            "metadata": {"ApiType": "Azure"},
        },
    }


def _subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _subset(value, actual[key])
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(expected) == len(actual)
            and all(_subset(left, right) for left, right in zip(expected, actual))
        )
    return expected == actual


def _connection_readback(
    plan: dict[str, Any], actual: dict[str, Any]
) -> tuple[bool, list[str]]:
    expected = connection_definition(plan)
    properties = actual.get("properties")
    expected_id = (
        f"{plan['project_resource_id']}/connections/{plan['connection']['name']}"
    )
    actual_id = actual.get("id")
    if (
        actual.get("name") != expected["name"]
        or (
            "id" in actual
            and (
                not isinstance(actual_id, str)
                or actual_id.casefold() != expected_id.casefold()
            )
        )
        or not isinstance(properties, dict)
    ):
        return False, []
    required = {
        key: value
        for key, value in expected["properties"].items()
        if key != "isSharedToAll"
    }
    if not _subset(required, properties):
        return False, []

    expected_sharing = expected["properties"]["isSharedToAll"]
    actual_sharing = properties.get("isSharedToAll")
    if not isinstance(actual_sharing, bool) or (
        actual_sharing and not expected_sharing
    ):
        return False, []
    if not expected_sharing and properties.get("sharedUserList", []) != []:
        return False, []
    warnings = []
    if actual.get("type") != expected["type"]:
        warnings.append(
            "connection-type-metadata-differs: ARM type metadata differs from the "
            "Foundry project type; the exact resource path and binding were checked."
        )
    if expected_sharing and not actual_sharing:
        warnings.append(
            "connection-sharing-restricted: requested isSharedToAll=true but Azure "
            "returned false; retained without widening access. Agent invocation "
            "is required to verify usability."
        )
    return True, warnings


def connection_leaf(value: Any) -> str:
    return str(value or "").rstrip("/").rsplit("/", 1)[-1]


def normalized_tool(value: dict[str, Any]) -> dict[str, Any]:
    names = value.get("allowed_tools") or []
    if isinstance(names, dict):
        names = names.get("tool_names") or []
    return {
        "type": str(value.get("type") or "").lower(),
        "server_label": value.get("server_label"),
        "server_url": value.get("server_url"),
        "project_connection_id": connection_leaf(
            value.get("project_connection_id")
        ),
        "allowed_tools": sorted(names),
        "require_approval": str(value.get("require_approval") or "").lower(),
        "headers": dict(sorted((value.get("headers") or {}).items())),
    }


def normalized_agent_definition(
    value: dict[str, Any], server_label: str
) -> dict[str, Any]:
    normalized = json.loads(json.dumps(value))
    for tool in normalized.get("tools") or []:
        if (
            not isinstance(tool, dict)
            or tool.get("type") != "mcp"
            or tool.get("server_label") != server_label
        ):
            continue
        allowed = tool.get("allowed_tools")
        if isinstance(allowed, list):
            tool["allowed_tools"] = {"tool_names": allowed}
        elif isinstance(allowed, dict) and allowed.get("read_only") is None:
            allowed.pop("read_only", None)
    return normalized


def desired_agent_definition(
    current: dict[str, Any],
    expected_tool: dict[str, Any],
    expected_structured_input: tuple[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], bool]:
    desired = json.loads(json.dumps(current))
    tools = list(desired.get("tools") or [])
    same_label = [
        tool
        for tool in tools
        if tool.get("server_label") == expected_tool.get("server_label")
    ]
    if len(same_label) > 1:
        raise HelperFailure(
            "duplicate-tool-label",
            "More than one knowledge-base MCP tool uses the approved label.",
            blocked_at="reconciliation",
        )
    if same_label and normalized_tool(same_label[0]) != normalized_tool(expected_tool):
        raise HelperFailure(
            "agent-definition-drift",
            "The existing same-label MCP tool conflicts with the approved binding.",
            blocked_at="reconciliation",
        )
    instructions = str(desired.get("instructions") or "").rstrip()
    structured_exact = True
    if expected_structured_input is not None:
        input_name, input_definition = expected_structured_input
        structured_inputs = desired.get("structured_inputs") or {}
        if not isinstance(structured_inputs, dict):
            raise HelperFailure(
                "agent-definition-drift",
                "Existing structured inputs are not an object.",
                blocked_at="reconciliation",
            )
        current_input = structured_inputs.get(input_name)
        if current_input is not None and current_input != input_definition:
            raise HelperFailure(
                "agent-definition-drift",
                "The permission-forwarding structured input conflicts with the approved binding.",
                blocked_at="reconciliation",
            )
        structured_exact = current_input == input_definition
    tool_exact = bool(same_label)
    grounding_exact = GROUNDING in instructions
    if tool_exact and grounding_exact and structured_exact:
        return desired, False
    if not tool_exact:
        tools.append(expected_tool)
        desired["tools"] = tools
    if not grounding_exact:
        desired["instructions"] = f"{instructions}\n\n{GROUNDING}".strip()
    if expected_structured_input is not None and not structured_exact:
        input_name, input_definition = expected_structured_input
        structured_inputs = dict(desired.get("structured_inputs") or {})
        structured_inputs[input_name] = input_definition
        desired["structured_inputs"] = structured_inputs
    return desired, True


def _validate_plan(plan: dict[str, Any]) -> None:
    reject_secrets(plan)
    require_allowed_fields(plan, PLAN_FIELDS, label="Prompt connection plan")
    if plan.get("grounding_instructions") != GROUNDING:
        raise HelperFailure(
            "grounding-instructions-mismatch",
            "The plan must bind the current exact grounding_instructions; obtain new approval.",
            blocked_at="confirmation",
        )
    network = plan.get("network")
    if network is not None:
        if not isinstance(network, dict):
            raise HelperFailure(
                "input-schema-invalid",
                "network must be an object.",
                blocked_at="input-resolution",
            )
        require_allowed_fields(
            network,
            {"posture", "evidence"},
            label="network",
        )
    if plan.get("operation") != "connect":
        raise HelperFailure(
            "operation-invalid",
            "Prompt helper supports only operation connect.",
            blocked_at="input-resolution",
        )
    if plan.get("cleanup_approved") is not False:
        raise HelperFailure(
            "cleanup-boundary-invalid",
            "Connection approval must not include cleanup.",
            blocked_at="confirmation",
        )
    if plan.get("sdk_major") != 2:
        raise HelperFailure(
            "sdk-version-invalid",
            "The approved plan must bind azure-ai-projects major version 2.",
            blocked_at="input-resolution",
        )
    _project_identity(plan)
    connection = plan.get("connection")
    agent = plan.get("agent")
    rbac = plan.get("rbac_verified")
    if not isinstance(connection, dict) or not isinstance(agent, dict):
        raise HelperFailure(
            "input-schema-invalid",
            "connection and agent objects are required.",
            blocked_at="input-resolution",
        )
    require_allowed_fields(
        connection,
        {"name", "target", "action", "expected_etag", "is_shared_to_all"},
        label="Prompt connection target",
    )
    if not isinstance(connection.get("is_shared_to_all", True), bool):
        raise HelperFailure(
            "connection-invalid",
            "connection.is_shared_to_all must be a boolean.",
            blocked_at="input-resolution",
        )
    require_allowed_fields(
        agent,
        {"name", "version", "model", "expected_definition_digest"},
        label="Prompt agent target",
    )
    target = connection.get("target")
    parsed_target = urlsplit(target) if isinstance(target, str) else None
    if (
        parsed_target is None
        or parsed_target.scheme != "https"
        or parsed_target.hostname is None
        or SEARCH_HOST.fullmatch(parsed_target.hostname) is None
        or KB_MCP_PATH.fullmatch(parsed_target.path) is None
        or parse_qs(parsed_target.query) != {"api-version": ["2026-08-01-preview"]}
        or parsed_target.fragment
        or parsed_target.username
        or parsed_target.password
        or parsed_target.port not in {None, 443}
    ):
        raise HelperFailure(
            "connection-invalid",
            "Connection target must be the exact preview knowledge-base MCP endpoint.",
            blocked_at="input-resolution",
        )
    if connection.get("action") not in {"create", "update", "reuse"}:
        raise HelperFailure(
            "connection-invalid",
            "connection.action must be create, update, or reuse.",
            blocked_at="input-resolution",
        )
    if plan.get("allowed_tools") != ["knowledge_base_retrieve"]:
        raise HelperFailure(
            "tool-policy-invalid",
            "allowed_tools must contain only knowledge_base_retrieve.",
            blocked_at="input-resolution",
        )
    if plan.get("require_approval") != "never":
        raise HelperFailure(
            "tool-policy-invalid",
            "The approved base-only MCP tool policy requires require_approval never.",
            blocked_at="input-resolution",
        )
    forwarding = plan.get("permission_forwarding")
    if not isinstance(forwarding, dict) or forwarding.get("mode") not in {
        "not-applicable",
        "structured-input",
    }:
        raise HelperFailure(
            "permission-forwarding-invalid",
            "permission_forwarding.mode must be not-applicable or structured-input.",
            blocked_at="input-resolution",
        )
    require_allowed_fields(
        forwarding,
        {"mode", "name"},
        label="Permission forwarding",
    )
    if forwarding["mode"] == "structured-input" and forwarding.get("name") != (
        "search_auth_token"
    ):
        raise HelperFailure(
            "permission-forwarding-invalid",
            "Permission forwarding requires the search_auth_token structured input.",
            blocked_at="input-resolution",
        )
    required_agent = {
        "name",
        "version",
        "model",
        "expected_definition_digest",
    }
    if not required_agent.issubset(agent) or not all(
        isinstance(agent[field], str) and agent[field]
        for field in required_agent
    ):
        raise HelperFailure(
            "agent-invalid",
            "Agent name, version, model, and expected definition digest are required.",
            blocked_at="input-resolution",
        )
    if (
        not isinstance(rbac, dict)
        or rbac.get("verified") is not True
        or not rbac.get("assignment_id")
        or not rbac.get("principal_id")
        or not rbac.get("scope")
        or rbac.get("role") != "Search Index Data Reader"
    ):
        raise HelperFailure(
            "rbac-unverified",
            "Exact Search Index Data Reader assignment readback is required.",
            blocked_at="reconciliation",
        )
    require_allowed_fields(
        rbac,
        {"verified", "assignment_id", "principal_id", "role", "scope"},
        label="RBAC verification",
    )
    if SHA256.fullmatch(agent["expected_definition_digest"]) is None:
        raise HelperFailure(
            "agent-invalid",
            "expected_definition_digest must be a canonical SHA-256 digest.",
            blocked_at="input-resolution",
        )


def _reconcile_connection(
    plan: dict[str, Any],
    token: str,
    *,
    transport: Transport,
) -> tuple[str, dict[str, Any], list[str]]:
    url = _connection_url(plan)
    desired = connection_definition(plan)
    request_ids: list[str] = []
    try:
        current_result = transport("GET", url, token)
        current = current_result.body
        if current_result.request_id:
            request_ids.append(current_result.request_id)
    except HelperFailure as failure:
        if failure.http_status != 404:
            raise
        current = None
        if failure.request_id:
            request_ids.append(failure.request_id)
    if current is not None and not isinstance(current, dict):
        raise HelperFailure(
            "connection-readback-invalid",
            "Project connection readback was not a JSON object.",
            blocked_at="reconciliation",
        )
    if current is not None and _connection_readback(plan, current)[0]:
        return "reused", current, request_ids

    action = plan["connection"]["action"]
    headers = {"Content-Type": "application/json"}
    if current is None:
        if action != "create":
            raise HelperFailure(
                "connection-absent",
                "The approved non-create connection target is absent.",
                blocked_at="reconciliation",
            )
        headers["If-None-Match"] = "*"
        completed_action = "created"
    else:
        if action != "update":
            raise HelperFailure(
                "connection-conflict",
                "A non-equivalent connection cannot be overwritten.",
                blocked_at="reconciliation",
            )
        etag = current.get("etag") or current.get("@odata.etag")
        if not etag or etag != plan["connection"].get("expected_etag"):
            raise HelperFailure(
                "connection-drift",
                "Connection ETag changed after approval.",
                blocked_at="reconciliation",
            )
        headers["If-Match"] = etag
        completed_action = "updated"

    try:
        result = transport(
            "PUT",
            url,
            token,
            body=canonical_bytes(desired),
            headers=headers,
        )
    except HelperFailure as failure:
        if not is_ambiguous_mutation_failure(failure):
            raise
        return _recover_ambiguous_connection(
            plan,
            url,
            token,
            desired,
            completed_action,
            request_ids,
            failure,
            transport=transport,
        )
    if result.status not in {200, 201}:
        if result.status in {408, 429} or result.status >= 500:
            return _recover_ambiguous_connection(
                plan,
                url,
                token,
                desired,
                completed_action,
                request_ids,
                HelperFailure(
                    "connection-outcome-ambiguous",
                    f"Connection mutation returned ambiguous HTTP {result.status}.",
                    blocked_at="execution",
                    request_id=result.request_id,
                    status=result.status,
                    partial=True,
                ),
                transport=transport,
            )
        raise HelperFailure(
            "connection-mutation-failed",
            f"Connection create or update returned HTTP {result.status}.",
            blocked_at="execution",
            request_id=result.request_id,
            status=result.status,
        )
    if result.request_id:
        request_ids.append(result.request_id)
    write = {"action": completed_action, "connection": desired["name"]}
    try:
        readback = transport("GET", url, token)
    except HelperFailure as failure:
        raise HelperFailure(
            failure.code,
            failure.message,
            blocked_at=failure.blocked_at,
            writes=[write, *failure.writes],
            resources_remaining=[
                {
                    "type": "project-connection",
                    "name": plan["connection"]["name"],
                }
            ],
            request_id=failure.request_id,
            status=failure.http_status,
            partial=True,
        ) from failure
    if readback.request_id:
        request_ids.append(readback.request_id)
    if readback.status != 200 or not isinstance(readback.body, dict):
        raise HelperFailure(
            "connection-readback-invalid",
            "Connection readback did not return one JSON object.",
            blocked_at="verification",
            writes=[write],
            resources_remaining=[
                {
                    "type": "project-connection",
                    "name": plan["connection"]["name"],
                }
            ],
            request_id=readback.request_id,
            partial=True,
        )
    if not _connection_readback(plan, readback.body)[0]:
        raise HelperFailure(
            "connection-readback-mismatch",
            "Connection readback does not match the approved definition.",
            blocked_at="verification",
            writes=[write],
            resources_remaining=[
                {
                    "type": "project-connection",
                    "name": plan["connection"]["name"],
                }
            ],
            request_id=readback.request_id,
            partial=True,
        )
    return completed_action, readback.body, request_ids


def _recover_ambiguous_connection(
    plan: dict[str, Any],
    url: str,
    token: str,
    desired: dict[str, Any],
    completed_action: str,
    request_ids: list[str],
    failure: HelperFailure,
    *,
    transport: Transport,
) -> tuple[str, dict[str, Any], list[str]]:
    identity = {
        "type": "project-connection",
        "name": plan["connection"]["name"],
    }
    if failure.request_id:
        request_ids.append(failure.request_id)
    try:
        readback = transport("GET", url, token)
    except HelperFailure as readback_failure:
        raise HelperFailure(
            "connection-outcome-ambiguous",
            "Connection mutation and same-identity readback are ambiguous.",
            blocked_at="verification",
            resources_remaining=[identity],
            request_id=readback_failure.request_id or failure.request_id,
            status=failure.http_status,
            partial=True,
        ) from readback_failure
    if readback.request_id:
        request_ids.append(readback.request_id)
    if (
        readback.status != 200
        or not isinstance(readback.body, dict)
        or not _connection_readback(plan, readback.body)[0]
    ):
        raise HelperFailure(
            "connection-outcome-ambiguous",
            "Same-identity readback did not prove the approved connection mutation.",
            blocked_at="verification",
            resources_remaining=[identity],
            request_id=readback.request_id or failure.request_id,
            status=failure.http_status,
            partial=True,
        )
    return completed_action, readback.body, request_ids


def _load_sdk() -> tuple[Any, Any, Any, Any, Any]:
    try:
        if version("azure-ai-projects").split(".", 1)[0] != SDK_MAJOR:
            raise HelperFailure(
                "sdk-version-invalid",
                "azure-ai-projects 2.x is required.",
                blocked_at="execution",
            )
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import (
            MCPTool,
            PromptAgentDefinition,
            StructuredInputDefinition,
        )
        from azure.core.exceptions import AzureError
        from azure.identity import AzureCliCredential
    except PackageNotFoundError as exc:
        raise HelperFailure(
            "sdk-unavailable",
            "azure-ai-projects 2.x is not installed.",
            blocked_at="execution",
        ) from exc
    except ImportError as exc:
        raise HelperFailure(
            "sdk-unavailable",
            "azure-ai-projects, azure-identity, and azure-core are required.",
            blocked_at="execution",
        ) from exc
    return (
        AIProjectClient,
        MCPTool,
        PromptAgentDefinition,
        StructuredInputDefinition,
        (AzureCliCredential, AzureError),
    )


def _connect_agent(
    plan: dict[str, Any],
    *,
    sdk_loader: Callable[[], tuple[Any, Any, Any, Any, Any]] = _load_sdk,
) -> tuple[str, dict[str, Any]]:
    (
        AIProjectClient,
        MCPTool,
        PromptAgentDefinition,
        StructuredInputDefinition,
        extras,
    ) = sdk_loader()
    AzureCliCredential, AzureError = extras
    agent = plan["agent"]
    connection = plan["connection"]
    created_write: dict[str, Any] | None = None
    client = AIProjectClient(
        endpoint=_project_endpoint(plan["project_endpoint"]),
        credential=AzureCliCredential(),
    )
    try:
        versions = list(client.agents.list_versions(agent_name=agent["name"]))
        if agent["version"] not in {str(item.version) for item in versions}:
            raise HelperFailure(
                "agent-version-absent",
                "The exact existing Prompt Agent version was not found.",
                blocked_at="reconciliation",
            )
        current = client.agents.get_version(
            agent_name=agent["name"],
            agent_version=agent["version"],
        )
        current_definition = current.definition.as_dict()
        if (
            current_definition.get("kind") != "prompt"
            or current_definition.get("model") != agent["model"]
        ):
            raise HelperFailure(
                "agent-definition-drift",
                "Agent type or model differs from the approved plan.",
                blocked_at="reconciliation",
            )
        if digest(current_definition) != agent["expected_definition_digest"]:
            raise HelperFailure(
                "agent-definition-drift",
                "Agent definition digest changed after approval.",
                blocked_at="reconciliation",
            )
        tool_arguments = {
            "server_label": "knowledge-base",
            "server_url": connection["target"],
            "project_connection_id": connection["name"],
            "allowed_tools": plan["allowed_tools"],
            "require_approval": plan["require_approval"],
        }
        expected_structured_input = None
        if plan["permission_forwarding"]["mode"] == "structured-input":
            input_name = plan["permission_forwarding"]["name"]
            tool_arguments["headers"] = {
                "x-ms-query-source-authorization": f"{{{{{input_name}}}}}"
            }
            input_definition = StructuredInputDefinition(
                description="Per-user Azure AI Search bearer token",
                required=True,
                schema={"type": "string"},
            ).as_dict()
            expected_structured_input = (input_name, input_definition)
        expected_tool = MCPTool(
            **tool_arguments,
        ).as_dict()
        desired, changed = desired_agent_definition(
            current_definition,
            expected_tool,
            expected_structured_input,
        )
        normalized_desired = normalized_agent_definition(
            desired, tool_arguments["server_label"]
        )
        if not changed:
            return "reused", {
                "name": agent["name"],
                "version": agent["version"],
                "definition_digest": digest(current_definition),
            }
        exact_versions = []
        for version_id in sorted(
            {
                str(item.version)
                for item in versions
                if str(item.version) != agent["version"]
            }
        ):
            candidate = client.agents.get_version(
                agent_name=agent["name"],
                agent_version=version_id,
            )
            candidate_definition = candidate.definition.as_dict()
            if normalized_agent_definition(
                candidate_definition, tool_arguments["server_label"]
            ) == normalized_desired:
                exact_versions.append(
                    {
                        "name": agent["name"],
                        "version": version_id,
                        "definition_digest": digest(candidate_definition),
                    }
                )
        if len(exact_versions) > 1:
            raise HelperFailure(
                "duplicate-desired-agent-version",
                "More than one existing Prompt Agent version matches the approved result.",
                blocked_at="reconciliation",
            )
        if exact_versions:
            return "reused", exact_versions[0]
        try:
            updated = client.agents.create_version(
                agent_name=agent["name"],
                definition=PromptAgentDefinition(**desired),
            )
        except AzureError as exc:
            if not is_ambiguous_sdk_error(exc):
                raise HelperFailure(
                    message="The Prompt Agent SDK create operation failed.",
                    blocked_at="execution",
                    **sdk_error_metadata(exc, "agent-sdk-failed"),
                ) from exc
            identity = {
                "type": "prompt-agent-version",
                "name": agent["name"],
                "definition_digest": digest(desired),
            }
            try:
                matches = []
                for item in client.agents.list_versions(agent_name=agent["name"]):
                    candidate = client.agents.get_version(
                        agent_name=agent["name"],
                        agent_version=str(item.version),
                    )
                    candidate_definition = candidate.definition.as_dict()
                    if normalized_agent_definition(
                        candidate_definition, tool_arguments["server_label"]
                    ) == normalized_desired:
                        matches.append(
                            {
                                "name": agent["name"],
                                "version": str(item.version),
                                "definition_digest": digest(candidate_definition),
                            }
                        )
            except AzureError as readback_exc:
                raise HelperFailure(
                    "agent-create-outcome-ambiguous",
                    "Agent version creation and same-identity readback are ambiguous.",
                    blocked_at="verification",
                    resources_remaining=[identity],
                    partial=True,
                    **sdk_error_metadata(exc),
                ) from readback_exc
            if len(matches) == 1:
                return "created", matches[0]
            raise HelperFailure(
                "agent-create-outcome-ambiguous",
                "Same-agent readback did not identify exactly one approved version.",
                blocked_at="verification",
                resources_remaining=[identity],
                partial=True,
                **sdk_error_metadata(exc),
            ) from exc
        created_write = {
            "action": "created",
            "agent": str(updated.name),
            "version": str(updated.version),
        }
        created_identity = {
            "type": "prompt-agent-version",
            "name": str(updated.name),
            "version": str(updated.version),
        }
        try:
            readback = client.agents.get_version(
                agent_name=updated.name,
                agent_version=str(updated.version),
            )
            readback_definition = readback.definition.as_dict()
            expected_definition, changed_after = desired_agent_definition(
                readback_definition,
                expected_tool,
                expected_structured_input,
            )
            if (
                changed_after
                or expected_definition != readback_definition
                or normalized_agent_definition(
                    readback_definition, tool_arguments["server_label"]
                ) != normalized_desired
            ):
                raise HelperFailure(
                    "agent-readback-mismatch",
                    "Created version differs from the approved definition or tool and grounding delta.",
                    blocked_at="verification",
                )
        except HelperFailure as failure:
            raise HelperFailure(
                failure.code,
                failure.message,
                blocked_at=failure.blocked_at,
                writes=[created_write, *failure.writes],
                resources_remaining=[
                    created_identity,
                    *[
                        item
                        for item in failure.resources_remaining
                        if item != created_identity
                    ],
                ],
                request_id=failure.request_id,
                status=failure.http_status,
                partial=True,
            ) from failure
        return "created", {
            "name": updated.name,
            "version": str(updated.version),
            "definition_digest": digest(readback_definition),
        }
    except AzureError as exc:
        remaining = (
            [
                {
                    "type": "prompt-agent-version",
                    "name": created_write["agent"],
                    "version": created_write["version"],
                }
            ]
            if created_write is not None
            else []
        )
        raise HelperFailure(
            message="The Prompt Agent SDK operation failed.",
            blocked_at="execution",
            writes=[created_write] if created_write is not None else [],
            resources_remaining=remaining,
            partial=created_write is not None,
            **sdk_error_metadata(exc, "agent-sdk-failed"),
        ) from exc
    finally:
        client.close()


def execute(
    document: dict[str, Any],
    *,
    token_provider: TokenProvider = azure_cli_token,
    transport: Transport = http_request,
    sdk_loader: Callable[[], tuple[Any, Any, Any, Any, Any]] = _load_sdk,
) -> dict[str, Any]:
    plan = document["plan"]
    fingerprint = document["_computed_fingerprint"]
    _validate_plan(plan)
    token = token_provider(MANAGEMENT_AUDIENCE)
    connection_action, connection, request_ids = _reconcile_connection(
        plan,
        token,
        transport=transport,
    )
    connection_warnings = _connection_readback(plan, connection)[1]
    connection_write = (
        []
        if connection_action == "reused"
        else [{"action": connection_action, "connection": plan["connection"]["name"]}]
    )
    try:
        agent_action, agent = _connect_agent(plan, sdk_loader=sdk_loader)
    except HelperFailure as failure:
        raise HelperFailure(
            failure.code,
            failure.message,
            blocked_at=failure.blocked_at,
            writes=connection_write + failure.writes,
            resources_remaining=(
                (
                    [
                        {
                            "type": "project-connection",
                            "name": plan["connection"]["name"],
                        }
                    ]
                    if connection_write
                    else []
                )
                + failure.resources_remaining
            ),
            request_id=failure.request_id,
            status=failure.http_status,
            partial=bool(connection_write or failure.writes or failure.partial),
            warnings=connection_warnings + failure.warnings,
        ) from failure

    resources = {"created": [], "reused": [], "updated": [], "skipped": []}
    resources[connection_action].append(
        {"type": "project-connection", "name": plan["connection"]["name"]}
    )
    resources[agent_action].append({"type": "prompt-agent-version", **agent})
    return {
        "status": "completed",
        "outcome": str(plan.get("outcome") or "connect-existing-prompt-agent"),
        "approved_plan": {"fingerprint": fingerprint, "confirmed": True},
        "resources": resources,
        "api_contracts": [
            {
                "operation": "project-connection",
                "version": ARM_API_VERSION,
                "preview": True,
            },
            {
                "operation": "prompt-agent-version",
                "version": "azure-ai-projects-2.x",
                "preview": True,
            },
        ],
        "data_movement": {"boundary": "knowledge-base MCP retrieval", "result": "bound"},
        "auth": {"mode": "managed-identity", "principals": [plan["rbac_verified"]["principal_id"]]},
        "rbac": {"assignments": [plan["rbac_verified"]["assignment_id"]]},
        "network": plan.get("network", {"posture": "preserved", "evidence": None}),
        "verification": {
            "connection_readback": {
                "name": connection.get("name"),
                "definition_digest": digest(connection),
                "request_ids": request_ids,
                "actual_is_shared_to_all": connection["properties"]["isSharedToAll"],
            },
            "agent_readback": agent,
            "permission_forwarding": plan["permission_forwarding"],
            "idempotency": "compatible connection and exact tool/grounding state is zero-write",
            "agent_invocation": "not-run; required for end-to-end verification",
        },
        "warnings": connection_warnings,
        "ownership": {
            "run_owned": connection_write
            + ([{"type": "prompt-agent-version", **agent}] if agent_action == "created" else []),
            "reused_not_owned": (
                [{"type": "project-connection", "name": plan["connection"]["name"]}]
                if connection_action == "reused"
                else []
            )
            + ([{"type": "prompt-agent-version", **agent}] if agent_action == "reused" else []),
            "owner": plan.get("owner"),
        },
        "cleanup": {
            "status": "not-requested",
            "separate_confirmation_required": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    fingerprint: str | None = None
    owner: Any = None
    outcome = "connect-existing-prompt-agent"
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
