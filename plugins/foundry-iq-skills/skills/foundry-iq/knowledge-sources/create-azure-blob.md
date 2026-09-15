# Create a Blob or ADLS Gen2 knowledge source

## When to use

One Blob/ADLS boundary; [type/API rules](../references/platform-interfaces.md#source-formats).

## Do not use

No uploads, unselected boundaries or other connectors. Never modify objects.

## Inputs and discovery order

Execution checklist, not a questionnaire. Resolve prompt/session/workspace, then
`az account show` for caller/tenant/default subscription. Explicit scope wins;
never silently switch context. Missing CLI/sign-in blocks discovery, not proof of absence.
Reads need no approval except content inspection: exact sample authorization.
Silence is not approval.
Recommend; ask one focused question only for unresolved decisions.

| Input | Why needed | Required? | Discovery order | Safe default | If missing or unanswered | Reconfirmation trigger |
|---|---|---|---|---|---|---|
| Scope/Search/access | Target | Before write | Exact Azure GET | Recommend reuse/new | Offer choices | Scope/access |
| Storage/container/prefix | Data | Before inventory | URL/name/choices | No implicit root | Choose boundary | Scope |
| Objects/ETags/versions/ACLs | Drift | Required | Inventory | None | Discover/block | Objects/ACLs |
| Processing/API/models | Ingest/search | Required | Content/choice | No extraction default | Assess/choose | Content/mode |
| Owner/name/cost/network/cleanup | Owner | Required | Readback | Preserve | Approve plan | Owner/cost/access |

## Decisions

Unresolved Search: [owner](../search-services/create.md); others:
[bootstrap](../references/search-substrate.md). No routine policy reads.
Resume here; reuse Storage, never create data or a KB.

Names, container/folder URLs or unresolved accounts:
read [resource intake](../references/resource-intake.md); reuse derived fields.
After account selection, enumerate only unresolved containers:
`az storage container list --account-name <account>
--auth-mode login --subscription <sub> --num-results '*'`.
Known containers skip enumeration; validate the selected boundary directly.
Denied listing: ask for an exact container, never broaden access or infer absence.
Resolve only missing container/folder scope; root `""` requires explicit choice.
No object inventory/download before boundary selection.
No keys/SAS; missing Storage/content: separate provisioning/upload workflow.

Missing roles: [RBAC](../references/bootstrap-azure.md#roles-readiness-and-return).
Propose the least-privilege grant, obtain consent, read back, then resume planning.

Honor explicit processing choices only when informed and compatible.
Unknown content or mode/goal conflicts: read [content-fit](../references/content-fit.md).
MUST assess/clarify before planning: bounded authorized samples or questions about
searchable text versus scans/visuals/layout and answer dependence.
Reuse answers; honor informed reduced outcomes.
Unavailable/declined/unreadable inspection means ask, not assume text-only.
No filename/MIME inference, silent default/downgrade or model calls.
Explain tradeoffs; obtain concrete-plan/CU/data approvals.
Vectors are independent: hybrid adds semantic/paraphrase matching/embedding cost.
Do not download blobs to decide. Lexical skips vector references.

HNS selects ADLS; preserve case.
Blob non-root prefixes end in `/`; ADLS directories do not.
Arbitrary partial-name prefixes: never append `/` or widen.
GA `2026-04-01` minimal is Blob-only extractive; synthesis/agents/permissions
need approved preview. Permission retrieval forwards the caller's Entra token
per-request through `x-ms-query-source-authorization`, scoped to
`https://search.azure.com/.default`; never persist it.

Read [Blob contract](../helpers/blob-contracts.md); run read-only
`python helpers/blob_source.py --discover <selected-boundary.json>`.

## Proposed plan

```text
python helpers/blob_source.py --plan intent.json
```

[Intent](../helpers/blob-contracts.md#planning).
Bind dependencies/boundary/API/processing/access/read/poll limits;
public/system-assigned Search; no image verbalization, permissions or schedules.
Vectors use `processing: minimal-vector` and
[embedding choices](../helpers/vector-contracts.md).

### Opt-in Content Understanding

`processing: standard-cu`: read [CU branch](../helpers/blob-cu-contracts.md).
No provisioning/default-model/local-auth changes or probes.
`cu-prerequisite-missing`: return missing evidence to owner; never downgrade.
Combine source/CU/embedding cost/access/data approval.

Omit `embedding` for CU-only. Verify CU-capable
`services.ai.azure.com` region/required models/effective access, not existence.
Search's system identity needs Cognitive Services User on CU.
Embeddings may use another endpoint with separately verified access.
Storage stays ResourceId/keyless; no File keys/chat/asset store.
CU is independent of KB reasoning/synthesis.

Return `planned`, private `execution_input` (`approval.confirmed: false`),
`approval_summary`: changes/counts/bytes/processing/access/cost/ownership/cleanup.
Keep paths/ResourceId/ACLs/hashes private; no secrets. Verify access/requirements.

Exact reuse: no mutation approval or executor call. Read source,
observe selected Storage twice; reread source/ETag/generated IDs.
Redacted bindings need approved input/successful creation result matching fresh
ETag. Unproven provenance blocks; never infer accounts from containers.
Identity/inventory/ACL metadata is not ingestion readiness or retrieval.

## Confirmation

Keep immutable `plan_fingerprint`, `cleanup_approved: false`;
approve concrete changes, not hashes. Save only `execution_input`.
Refresh access/cost/data consent before mutations. Scope/object/access/definition/
model/ETag/known-requirement drift: rerun `--plan`, replace artifact and discard old consent.
Never edit nested plans or recompute hashes manually; receipts are not future consent.

## Mutation

New minimal or Standard/CU, with/without vectors: read [checkpoint/recheck](../references/blob-readiness-recheck.md);
resolve an existing operator-private directory and retain approved input there
before writes. Reuse needing readiness: read-only capture, never replay.

```text
python helpers/blob_source.py --input <approved-envelope.json> --receipt-dir <absolute-private-directory>
```

`reconcile-and-monitor` revalidates then creates/reuses. Never update drift,
suffix-create, change schedules, or patch children.
Source helpers never assign roles; unresolved access: bootstrap.
Private ADLS requires both `blob` and `dfs` links/DNS.

## Verification

Verify definition/ETag/generated readback and relevant completed cycle:
zero failed items. Unscheduled reuse/old success/`active` are not proof.
Inventories detect drift, not an atomic snapshot/lock; schedules evolve.
Embedding-enabled sources: [vector/query verification](../helpers/vector-contracts.md#read-only-verification-plan);
deployment proves neither readiness nor retrieval.

## Failure and partial completion

Preserve first failure/request ID. 403 is inaccessible, not absent.
Exit `2`: blocked/no-write; `3`: partial/remaining ownership/separate cleanup.
No alternate name or unapproved recreate.
Timeout/interruption: use the retained checkpoint; never replay creation.

## Cleanup

Separately approved `search_reconcile.py` deletes only the run-owned source
with current ETag/owned digest; Search deletes children.
Never delete Storage, objects or reused resources.
Role cleanup belongs to bootstrap under separate approval; unclear ownership blocks.

## Return contract

Return status/approval, IDs/evidence/readiness, failure/ownership/warnings/cleanup.
Pass assessment/uncertainty/answer needs/mode through prerequisites to the KB owner;
resume KB plus validated retrieval.

## References

Authorities: failure/conflict/uncertainty only.

[Official Blob procedure](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-blob).
[ADLS HEAD](https://learn.microsoft.com/rest/api/storageservices/datalakestoragegen2/path/get-properties).
