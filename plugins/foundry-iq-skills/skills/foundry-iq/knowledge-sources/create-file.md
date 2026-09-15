# Create a File knowledge source

## When to use

Direct upload to Search-managed storage; no customer Storage.

## Do not use

Changing/scheduled corpora, lifecycle/DLP/permissions or overflow:
[Blob/ADLS](create-azure-blob.md). Unsupported content blocks. Never stage to Blob,
split silently, alter files or upload outside the approved root.

## Inputs and discovery order

Execution checklist, not a questionnaire. Resolve prompt/session/workspace, then
`az account show` for caller/tenant/default subscription. Explicit scope wins;
never silently switch context. Missing CLI/sign-in blocks discovery, not proof of absence.
Reads need no approval except content inspection: exact sample authorization.
Silence is not approval.
Recommend; ask one focused question only for unresolved decisions.

| Input | Why needed | Required? | Discovery order | Safe default | If missing or unanswered | Reconfirmation trigger |
|---|---|---|---|---|---|---|
| Scope/Search/access | Target | Output before upload | Exact Azure GET | Recommend reuse/new | Offer choices | Scope/access |
| Root/inventory | Data | Before upload | Selection/listing | Never `.` | Choose root | Files |
| Owner/name/purpose/cleanup | Ownership | Before write | Task/readback | Propose names | Confirm owner | Ownership |
| Processing/models | Extraction/search | Required | Content/choice | No extraction default | Assess/choose | Content/mode |
| API/cost/network/consent | Security | Required | Readback | Preserve | Approve plan | Cost/access |

## Decisions

Unresolved Search: [owner](../search-services/create.md); others:
[bootstrap](../references/search-substrate.md). Resume after readback, never call Create KB.
No routine policy reads.
File-only creates no KB/synthesis model. Minimal lexical needs no model;
vectorization optionally adds embeddings; standard selects CU independently.

Honor explicit processing choices only when informed and compatible.
Unknown content or mode/goal conflicts: read [content-fit](../references/content-fit.md).
MUST assess/clarify before planning: bounded authorized samples or questions about
searchable text versus scans/visuals/layout and answer dependence.
Reuse answers; honor informed reduced outcomes.
Unavailable/declined/unreadable inspection means ask, not assume text-only.
No filename/MIME inference, silent default/downgrade or model calls.
Explain tradeoffs; obtain concrete-plan/CU/data approvals.
Vectors are independent: hybrid adds semantic/paraphrase matching/embedding cost.
Lexical skips vector references.

Reject absolute/traversing/unreadable entries or escaping links/reparse points.
Freeze relative path/MIME/bytes/mtime/SHA-256 in byte order; recheck before upload.

Prove formats, at most 200 files, per-file maximum: 50 MB for Free/Basic,
100 MB otherwise. Unknown/overflow: Blob.

- `minimal`: supported non-image content with `contentExtractionMode: minimal`.
- `standard`: `contentExtractionMode: standard`, `2026-08-01-preview`,
  CU and approved cost/security/data movement; source embeddings are optional.
  Detected images with minimal are invalid; never downgrade.

GET exact source; unresolved: list candidates. Read all file pages each run.
Reuse exact definition/inventory/index/markers.
Duplicates/inaccessible/drift block; no suffixing/upload repair.

## Proposed plan

Read [helper contracts](../helpers/contracts.md) before planning.

```text
python helpers/file_source.py --plan request.json
```

UTF-8 request:

```json
{"schema_version":"1.0","endpoint":"https://svc.search.windows.net","name":"manuals","owner":"owner@example.com","local_root":"C:\\data\\manuals","paths":["guide.txt"],"service_tier":"basic","extraction_mode":"minimal","vectorization":"none","rbac":{"assignments":[{"id":"<observed-role>","principalId":"<observed-principal>"}]},"network":{"posture":"<posture>","evidence":"<readback>"}}
```

Tier: `free`/`basic`/`dedicated`/`serverless`. Require RBAC and
`network.posture`/`network.evidence`.
`paths`: 1–200 unique relative POSIX paths, no globs; MIME is a hint.
See [type/API rules](../references/platform-interfaces.md#source-formats).
Vectors: `vectorization: azureOpenAI` with [embedding choices](../helpers/vector-contracts.md).
For standard planning, read [CU choices](../references/standard-cu.md); minimal skips it.

Exit `0`: `status: planned`, `plan_fingerprint`, `approval_summary`,
`execution_input`, request IDs, `writes_performed: []`.
Summary: paths/count/bytes, target/actions, processing/access/cost/retention/cleanup;
no absolute root or integrity hashes.
For creation save **only `execution_input`** (`approval.confirmed: false`).
Verify known/security requirements before consent; unapproved input blocks.
Fresh exact reuse sets `execution_required: false` and
`mutation_approval_required: false`: no approval or executor.
Reread definition/ETag after all file pages; markers are not readiness/retrieval.
No writes, installs, identity changes or cached consent.

## Confirmation

The machine artifact retains the immutable proposed mutation plan,
`plan_fingerprint` and `cleanup_approved: false`; users review concrete choices, not fingerprints.
Requirements/inventory/endpoint/API/model/identity/network/role
or definition/ETag drift invalidates consent. Rerun `--plan`, replace the saved
`execution_input` and discard old consent; approve only new actual mutations.
Never edit nested plans or recompute hashes manually.

## Mutation

After approval:

```text
python helpers/file_source.py --input <approved-envelope.json>
```

`reconcile-and-ingest` validates `source`/`ingestion` agreement before writes.
Trust definitive uploads; bulk-check inventory once.
Timeout/409/429/5xx: one immediate readback. Exit `2`: blocked; `3`: partial.
Never invoke children alone. Create only absent sources; reuse never uploads.
`fileParameters.ingestionParameters` binds `contentExtractionMode`;
omit `embeddingModel` for lexical, else bind observed azureOpenAI endpoint/deployment/model.
Standard binds `aiServices.uri`; disable image verbalization, omitting `chatCompletionModel`.

CU secret: approved out-of-band environment variable; never serialize/echo.
Block rather than downgrade to minimal.
File rejects `networkAccessMode`: one index, no indexer/schedule; never patch children.

List `/knowledgesources('<source-name>')/files`, upload only absent
exact inventory entries by multipart POST, and read stable file IDs.
Never modify/stage files, use Search/Storage keys/SAS, or rename an ambiguous retry.

## Verification

Require definition/mode/dependencies, count/path/type/size/hash-to-file-ID mapping,
zero ingestion failures, generated index/child ownership, keyless Search access,
network and unchanged inventory. Rerun discovery: stable IDs/zero writes.
For vectors use [staged verification](../helpers/vector-contracts.md);
deployment or lexical results aren't vector retrieval proof.

## Failure and partial completion

Preserve first operation/status/message/request ID. Inaccessible is not absent.
`blocked`: evidence/next decision, `writes_performed: []`; `partial`:
writes/unverified IDs/ownership/rollback and separate cleanup.

## Cleanup

A separate cleanup plan/approval deletes only run-owned source/generated children.
Never delete or alter local files, reused dependencies or shared roles.
Unclear ownership blocks. `helpers/search_reconcile.py` binds
`operation: delete`, owned definition digest and current ETag.

## Return contract

Return status/fingerprint, resource/file/generated IDs, API, boundary/inventory,
auth/RBAC/network, ingestion/idempotency, ownership/warnings/cleanup.
Pass assessment/uncertainty/answer needs/mode through prerequisites to the KB owner;
resume KB plus validated retrieval.
Never return content/credentials.

## References

- [Audit fields](../references/platform-contracts.md).

Authorities: failure/conflict/uncertainty only.

- [File source](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-file)
