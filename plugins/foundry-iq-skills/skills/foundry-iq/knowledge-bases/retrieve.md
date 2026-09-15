# Retrieve from a knowledge base

## When to use

Read-only queries to one existing KB; optional connected Prompt/Hosted Agent audit.

## Do not use

No creation/repair/sync/connection/RBAC/effort changes or cleanup.
Failures/drift: [Diagnose](../troubleshooting/diagnose.md).
Return only requested content; never credentials.

## Inputs and discovery order

Standalone KB queries use the Search REST retrieve action with Entra auth.
No MCP connection or agent required. First check for Azure CLI and signed-in
context: preserve `azure-authentication-failed` or `azure-cli-unavailable`.
Never install tools or switch identity implicitly. Capture identity reads
privately: `az account show --output json`; for a user,
`az ad signed-in-user show --query id --output tsv` (no subscription flag).

Never ask the user to paste or provide a token, credential, or key in chat.
Missing verified host auth blocks; a pasted token is not a remedy.

Resolve prompt/session/workspace/exact Azure readback, then one focused question.
Label evidence. Read-only discovery/retrieval need no approval; silence never
selects identity or permissions.

| Input | Why needed | Required? | Discovery order | Safe default | If missing or unanswered | Reconfirmation trigger |
|---|---|---|---|---|---|---|
| Search/base ID/endpoint | Target | Yes | Prompt/session/readback | None | Ask ambiguity | No writes |
| API; definition/mode | Shape | Yes | Creation evidence; GET | None | Ask/block | None |
| Query | Retrieval | Yes | Prompt | None | Ask | None |
| Caller | Permissions | Yes | Identity readback | None | Block | None |
| Forwarding | Permissions | Conditional | Source/base readback | None | Block | None |
| Original identity | Citation audit | Conditional | Inventory | None | Unverifiable | None |
| Unrelated question | Abstention audit | Conditional | Prompt | None | Not tested | None |
| Agent/tool identity | Tool audit | Conditional | Readback | None | Block | None |

## Decisions

GET base/source definitions; connection binding is not definition evidence.
Use the API from creation evidence or ask before GET; it isn't a returned field.
GA `2026-04-01` is extractive. Preserve observed output/effort.

If requested low/medium or synthesis needs KB/model changes, hand off to
[KB setup](create.md) for chat-model selection and separately approved deployment
and configuration. Do not mutate during retrieval or silently fall back to minimal.

Inspect source `ingestionPermissionOptions` in ingestion parameters; unknown
posture blocks. Permission-enabled retrieval requires per-request
`x-ms-query-source-authorization`, audience `https://search.azure.com/.default`,
separate from service auth. Forward only the verified same signed-in user's
token; otherwise `permission-forwarding-unavailable`. Never persist/log tokens;
do not pass the caller token as a CLI argument. Never query unfiltered as fallback.

## Proposed plan

State target/API/mode, caller/query/forwarding, citation identity and optional
audit; `mutation: none`.

## Confirmation

No approval gate. Writes require the owner's separate plan and confirmation.

## Mutation

None; never retry through another resource.

Standalone: use selected endpoint/name/API and observed effort. Query is JSON
data, never shell text. GA/preview minimal use `intents`; preview low/medium uses
`messages`. Never override mode/effort/models/source selection.

Invoke the packaged helper by its loaded skill path, not a path in the customer's
project. Do not read/copy its source or write a replacement script:

```text
python "<skill-dir>/helpers/knowledge_base_retrieve.py" --input "<request.json>"
```

For the definition GET, the UTF-8 JSON input is:

```json
{"operation":"get-knowledge-base","endpoint":"https://<service>.search.windows.net","name":"<kb>","api_version":"2026-08-01-preview"}
```

Read each selected source using the same fields with
`operation: get-knowledge-source` and its exact name. The helper performs OData
escaping; do not pre-encode names. After inspecting definitions and permissions,
use the observed effort and explicit forwarding choice:

```json
{"operation":"retrieve","endpoint":"https://<service>.search.windows.net","name":"<kb>","api_version":"2026-08-01-preview","effort":"minimal","query":"<question>","forward_permissions":false}
```

Use the selected GA/preview API, not the example blindly. These closed inputs
have no approval envelope or fingerprint. Never put credentials in the input.
Set `forward_permissions: true` only for the verified same signed-in user when
the source requires forwarding. The helper additionally checks CLI user type,
then acquires the token in memory. It never accepts a caller token as input.

The helper builds requests, retains HTTP status/request ID, disables redirects,
bounds response bytes, and never retries. Exit `0` emits `status: response-received`
with `http_status`, `request_id`, and `response_body`; it is not grounding or
end-to-end verification. Exit `2` emits `status: blocked` with the first
code/status/request ID, no writes/ownership or cleanup, even for ambiguous POST.
Never print tokens or raw diagnostics.

REST results contain `response`, `references`, and optional `activity`; they are
not MCP `result.content[]`. Parse all returned text blocks and reference IDs.
Activity errors or missing grounding are incomplete, not success. HTTP `206`
is rejected even with valid-looking content. No-support is valid; never fill
gaps from general knowledge.

For an explicitly requested agent audit, invoke the existing connected agent
through its supported host and verify its native per-KB
`knowledge_base_retrieve` call. Missing connection returns
`knowledge-base-mcp-endpoint-unavailable`; do not substitute REST as agent proof.
Never substitute a generic index query or the generic Azure MCP Server
`search_*` tool group for either path.

## Verification

Require original File path plus file ID or Blob/ADLS URL/path plus ETag/version
citations. For synthesis audits, read and apply the shared
[semantic abstention criteria](../references/abstention.md),
honoring any explicit exact-output contract.
GA/preview extractive audits require no supporting extracts: do not invent a
synthesized `I don't know`. Recheck resource identities and require
`before_after_snapshot_equal: true`.

## Failure and partial completion

Permission denial is inaccessible, not absence. Unexpected empty/wrong/stale
output routes to diagnosis without mutation. Never fabricate citations or
success; retrieval failure creates no resource ownership.

## Cleanup

Not applicable. No resource is created and no cleanup approval is offered.

## Return contract

Verified: `status: completed`, `outcome: knowledge-base-retrieval`,
`mutation: none`, KB/source IDs/endpoint/API/mode, `preview: true|false`,
caller/forwarding, requested
answer/citations, activity/tool evidence, warnings/latency, abstention
tested/evidence, before/after equality.
Otherwise return `status: blocked`, `blocked_at`, first status/message/request ID,
missing/conflicting input, safe next decision, `writes_performed: []`, no new
ownership and `cleanup: not-applicable`. Never report unavailable evidence as
verified or include credentials/raw diagnostics.

## References

- [Abstention criteria](../references/abstention.md): required for synthesis audits.
- Optional [audit schema](../references/platform-contracts.md) and
  [versions](../references/platform-interfaces.md); not required normal-path reads.

Authorities: failure/conflict/uncertainty only.

- [Retrieve using a knowledge base](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve)
