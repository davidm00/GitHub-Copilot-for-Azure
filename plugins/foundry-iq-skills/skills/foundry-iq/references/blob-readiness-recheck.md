# Read-only Blob readiness follow-up

Blob/ADLS creation and read-only follow-up; not write resumption,
KB/retrieval completion or cleanup consent.

## Coverage and retained evidence

| Situation | Supported outcome |
|---|---|
| New minimal/Standard/CU, lexical/vector | Checkpoint before polling; recheck after timeout/interruption |
| Exact reuse | Read-only observation checkpoint, no creation ownership/mutation consent |
| Legacy admitted wire-only modes, schedules/permission options | Configuration-bound recheck, not new settings or permission proof |
| Legacy timeout, ambiguous PUT, pre-checkpoint interruption/lost receipt | Cannot reconstruct original-run proof |

Blob uses GA `2026-04-01` or preview `2026-08-01-preview`; ADLS requires preview
and path/ACL checks. Require keyless/system-assigned bindings.
Asset stores, other identities/connectors and unsupported embedding kinds block.
CU planning still excludes schedules, permission ingestion and private networking;
recovery adds no mutations.

For **all new planner modes**, retain the unchanged approved input and run:

```text
python helpers/blob_source.py --input <original-approved.json> --receipt-dir <absolute-private-directory>
```

Use an existing operator-owned private directory outside the installed plugin.
The helper validates privacy and enabled CLI context using `az account show`
before cloud work; no directory creation, ACL changes or overwrites.
After acknowledged conditional PUT plus exact readback, before polling, it
GETs the source and four returned generated definitions. Record original
approval/owner, pre-write `not_before`, generated `operation_id`, request IDs,
source identity/ETag/definition, generated ETags/digests and CLI context digest.
No tokens, generated credentials, document text or ACLs are persisted.

The exclusively created/flushed `<operation_id>.blob-readiness.json` is immutable.
`recheck_checkpoint` returns its leaf filename, operation ID and integrity digest.
Pair it with original input; never reconstruct either. Post-write persistence
failure is `partial`, retaining ownership without polling, cleanup or write retry.

### Fresh reuse, not recovered creation

For reuse follow-up, retain private `execution_input` unchanged
(`approval.confirmed: false`):

```text
python helpers/blob_recheck.py --capture <reuse-input.json> --receipt-dir <absolute-private-directory>
```

Capture checks source/configuration/Storage/context and retains its cutoff/first cycle.
Exit `0`, `status: completed`, `outcome: blob-readiness-capture` means only
**checkpoint retained**: `readiness.status: unverified`, no writes, ownership or
polling. Return request IDs/reused identity. `--capture` rejects creation artifacts,
never retrofits cutoffs or proves ambiguous PUTs.

Creation schema: `1.0`; reuse: `1.1`, with `excluded_cycle`
(start/end or null when none observed). The historical
`creation` field holds reconciliation evidence: reuse has empty `resources.created`
and `ownership.run_owned`. Approved reuse execution also accepts `--receipt-dir`;
normal reuse needs neither executor nor mutation consent.

## Recheck only

```text
python helpers/blob_recheck.py --input <original-input.json> --receipt <operation_id.blob-readiness.json>
```

Files must be absolute, bounded private UTF-8 JSON. Reject links,
hardlinks, unproven privacy, malformed/duplicate fields, changed integrity,
approval/owner/plan mismatch and invalid ownership before cloud reads.

The enabled public-cloud CLI tenant/subscription/principal must
match before/after observation. No login/switching/grants; ARM/Storage/Search tokens
are ephemeral. This is not a credential lock or effective-permissions proof.

Cloud reads:

- Source `GET knowledgesources('{name}')` and `/status`, original API version.
- Four exact returned `datasources`, `indexers`, `skillsets`, `indexes`:
  `GET {collection}('{name}')?api-version={original-version}`.
- Existing bounded two-pass Storage inventories plus ADLS metadata HEADs,
  before and after monitoring; both must match the original inventory digest.

Configuration observations bracket inventory/status. Require
nonempty string ETags, unchanged source/generated identities and full generated
configuration digests. Indexer datasource/skillset/target-index and exact
interval/startTime schedule must match; schedules never get reset or edited.
Generated datasource must expose the exact ResourceId account/container/prefix,
type/system identity; redacted credentials block.
Redacted source bindings use retained acknowledged creation evidence; fresh reuse
capture lacks that creation proof and requires a visible source ResourceId.
Normal reuse planning can still use its successful creation receipt.
Missing/denied/drift/redaction changes block.

Standard/CU readback uses the existing endpoint/auth verifier. Legacy wire-only
selectors come from original definitions, not invented prerequisites.
Masked/nonempty/malformed keys or changed identities block.
No CU/embedding calls or vector-query claims.

Reuse `blob_source.monitor` with the retained cutoff and original bounded limits.
Reuse additionally excludes its **retained** first completion, comparing normalized
times, never substituting the latest cycle. Require a
completed nonempty zero-failure/zero-skip cycle, valid interval/counters, no
relevant errors/current synchronization and no future completion. Stale/unrelated,
active, denied, missing or malformed evidence blocks. Only existing transient GET
retries apply. Unscheduled reuse without a new cycle stays blocked.
No indexer run/reset/history, document/model calls, PUT/PATCH/DELETE or data/RBAC changes.

## Output, progress and caller completion

Exit `0`, `blob-readiness-recheck`: source readiness only.
`original_run` retains action, operation, cutoff, plan/evidence digests, historical
IDs and ownership; fresh IDs are `read_only_evidence.request_ids`.
`writes_performed: []`; follow-up owns no resources.
`retrieval: unverified`, `knowledge_base: not-verified` remain explicit.

Exit `2`: blocked, not reversal of partial creation. Preserve resources/evidence
and first failure/status/request ID; later drift invalidates success.
Never synthesize missing errors/IDs; retain original failure output separately
because checkpoints precede polling.

CLI uses [shared sanitized stderr progress](../helpers/contracts.md#common-envelope-and-process-contract);
`--no-progress` suppresses it. Libraries are silent unless given
`Progress("blob-recheck")` or `Progress("blob-capture")`. One reporter/terminal event,
finite stages, no private values/ETA. One stdout JSON; broken stderr adds the
shared warning without changing results/calls/ownership/cleanup.

**Legacy limitation:** timeouts discarded cutoff/binding. Without a checkpoint,
existence cannot prove original ownership/readiness. Fresh reuse is a different
operation, not recovered historical success.
No service operation/revision ID correlates a qualifying cycle to its initiator.
Local integrity is not a service signature; observations are not locks.
Clock skew/concurrency can block.

Checkpoints/rechecks cannot replace [nonempty creation proof](blob-vector-readiness.md)
for zero-work reuse; never relabel them.
Return to the caller to finish authorized vector verification, KB attachment,
retrieval and agent steps under their owners; refresh drifted consent and obtain
outstanding query/write approval. Source readiness is not task completion.
Cleanup needs separate approval/fresh ownership/ETags; preserve shared resources,
customer data and roles.

## References

[Blob helper contract](../helpers/blob-contracts.md) owns ingestion/inventory semantics.
Authorities: failure/conflict/uncertainty only.
[Indexer GET](https://learn.microsoft.com/rest/api/searchservice/indexers/get?view=rest-searchservice-2026-04-01)
and [datasource GET](https://learn.microsoft.com/rest/api/searchservice/data-sources/get?view=rest-searchservice-2026-04-01)
define generated bindings.
