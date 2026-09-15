# Deterministic helper contracts

Read once before planning/approval; discover after boundary selection.
Require explicit modes; owners assess content fit/ambiguity/roles/approval/tradeoffs.
Invoke; inspect helper source only on `blocked`/`partial`.

## Common envelope and process contract

Input: UTF-8 JSON:

```json
{"schema_version":"1.0","plan":{},"approval":{"confirmed":true,"fingerprint":"sha256:<canonical-plan-digest>"}}
```

Canonical JSON: UTF-8, key-sorted, ASCII-escaped, compact. Approve the unchanged
plan; helpers verify fingerprints. Exclude credentials, tokens, keys, SAS,
passwords, content and secret-bearing connection strings.
Use signed-in CLI tokens. File standard alone permits secret environment variables;
bind names, never values.
Envelope, approval, plan, nested controls and file records are
closed schemas: undeclared fields block before authentication.
`desired` remains a complete service body. Results recursively redact secret fields.
Azure Policy evaluation belongs to the creation owner, not these helpers.
[Bootstrap](bootstrap-contracts.md): no preflight policy reads.
Bind known requirements and child fingerprint in the parent plan; no policy precheck.
Never add undeclared policy/tag fields; if required settings cannot reach the supported request body,
return `azure-policy-setting-unsupported` before creation.

Mutation commands emit compact JSON to stdout: exit `0` is `completed`, `2` no-write `blocked`,
`3` written/ambiguous `partial`. Preserve JSON/exit status.
After ambiguous PUT/POST/DELETE/SDK writes, read the same identity.
Only proven approved state/absence completes; otherwise `partial` with
`resources_remaining.run_owned`.

File/Blob/ADLS and Search apply: [_progress.py](_progress.py):
stderr JSONL; `--no-progress` disables. Planning/discovery stays quiet.
Libraries: `progress=Progress("<workflow>")`; children share one terminal event.
Finite activity/remaining checks, elapsed seconds, observed counts.
Same stage: once/second; transitions/terminal: immediate.
No heartbeat, background polling or ETA. Upload/readback isn't ingestion;
cycle updates aren't unique documents; ARM readiness isn't KB/retrieval/data-plane proof.
I/O failure: `progress-output-failed` warning; primary failures/execution unchanged.
Failed native stderr drains to null at shutdown; custom sinks untouched. Final JSON is authoritative.

## File source application

`python helpers/file_source.py --plan request.json`: read-only;
unapproved `execution_input`/`approval_summary`; exit `0` is `planned`, not readiness.
See [request/example](../knowledge-sources/create-file.md#proposed-plan).
Require `extraction_mode`; [optional embeddings](vector-contracts.md) are independent.
Planning: no bootstrap/roles/uploads/cleanup/approval; owner-owned requirements.
Fresh exact reuse sets `execution_required`/`mutation_approval_required` false;
no approval/execution. Creation requires consent to the unchanged envelope:

```text
python helpers/file_source.py --input <approved-envelope.json>
```

The parent requires `operation: reconcile-and-ingest`, `cleanup_approved: false`,
`owner`, `source` and `ingestion`. Children target the same endpoint/name/API/owner.
Validate both before mutation; reconcile before upload/readback.
Ingestion failure after creation is `partial`, retaining the write.
Reuse requires exact markers, never new files or per-file cleanup.
Invoke the parent, not children. `source` uses the
[reconciliation shape](#search-resource-reconciliation) with `kind: "file"`;
`ingestion`:

```json
{"operation":"ingest","endpoint":"https://svc.search.windows.net","name":"src","api_version":"2026-08-01-preview","local_root":"<root>","service_tier":"basic","extraction_mode":"minimal","owner":"o@x","cleanup_approved":false,"files":[{"path":"guide.txt","size":123,"mtime_ns":1700000000000000000,"sha256":"sha256:<64-hex>","media_type":"text/plain"}],"inventory_digest":"sha256:<64-hex>","expected_server_inventory_digest":"sha256:<64-hex>"}
```

## Search resource reconciliation

```text
python helpers/search_reconcile.py --input <approved-envelope.json>
```

Require `operation: reconcile`, `outcome`, `resource_type`, `endpoint`, `name`,
`api_version`, `action`, complete approved `desired`, `owner`, and
`cleanup_approved: false`. Use `action: create`, or approved `action: update`
with `expected_etag`. Exact existing state is zero-write.

Blob/ADLS plans also require `source_evidence` with `verified: true` and an
`inventory_digest`. ADLS requires `path_verified: true`, `acl_verified: true`.
These attest reconciliation, not evidence collection/readiness: apply through
the Blob parent below. File `standard` requires
`ai_services_api_key_environment`; set that named variable out of band.

KB plans bind `verified_source` (`verified: true`, source `name`, normalized
`definition_digest`); fresh same-API source GET must match before create/update/reuse.
GA omits preview fields/models. Preview binds output/effort; synthesis or
low/medium needs one model, including extractive output.
Model-free agent retrieval requires explicit preview minimal/extractive;
GA defaults are not MCP proof.

For Search cleanup, use the same command with `operation: delete`,
`plan_kind: cleanup`, `cleanup_approved: true`, `expected_etag`, and
`owned_definition_digest`. Use separately approved run-owned readback; delete only that identity
and verify absence.

## Blob/ADLS source application

Blob/ADLS alone loads [folder scope/bounds/drift/cleanup](blob-contracts.md).
`blob_source.py --discover` inventories; `--plan` builds unapproved artifacts
or verifies approval-free reuse;
`--input` applies the approved parent and monitors ingestion. Search
reconciliation alone never proves Blob readiness.

## File ingestion internals

`file_source.py` invokes this child after validating both plans.
Standalone CLI never authorizes new uploads.

Use the ingestion shape: absolute `local_root`, sorted unique
files with normalized relative paths, positive sizes, timestamps, digests, MIME
hints and optional string metadata. Reject path/inventory/extraction/
server-state/marker drift. Upload absent files sequentially; trust definitive
responses, then verify complete inventory once. Timeout/409/429/5xx alone:
immediate single-file readback. Never return bytes/local root.

## Existing Prompt Agent fallback

Only for unavailable MCP/missing connection/version operations;
never authorization denial/conflicting state:

```text
python helpers/prompt_connect.py --input <approved-envelope.json>
```

The plan requires `operation: connect`, `sdk_major: 2`, exact project resource
ID and matching endpoint identity, `connection`, `agent`, `rbac_verified`, `allowed_tools:
["knowledge_base_retrieve"]`, `require_approval: "never"`,
`permission_forwarding`, `owner`, and `cleanup_approved: false`. Bind the exact
existing version/digest and `grounding_instructions` from the
[selected fallback](../agents/connect-prompt-sdk-fallback.md); old text needs new
approval before authentication. Permission forwarding
is either `{"mode":"not-applicable"}` or
`{"mode":"structured-input","name":"search_auth_token"}`.
Reuse the sole complete approved match before creation; multiple matches block.
ARM uses `Microsoft.CognitiveServices/accounts/projects/connections`.
Optional boolean `connection.is_shared_to_all` defaults to `true`.
Fallback defines normalization/bounded warnings for creation,
ambiguous-write recovery/reuse. `agent_invocation: not-run` isn't E2E proof.

Separate Prompt cleanup:

```text
python helpers/prompt_cleanup.py --input <approved-envelope.json>
```

Use `operation: delete`, `plan_kind: cleanup`, `cleanup_approved: true`,
`sdk_major: 2`, exact project identity, and at least one `agent` or `connection`
object with `run_owned: true`, exact identity and `owned_definition_digest`;
connections also bind `expected_etag`. Delete the owned version before its
connection; verify absence. Preserve prior versions/project/model/KB/roles.
