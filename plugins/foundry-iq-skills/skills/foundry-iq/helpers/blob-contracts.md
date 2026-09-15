# Conditional Blob/ADLS helper contract

Apply: [shared stderr progress](contracts.md#common-envelope-and-process-contract);
`--no-progress` disables it. No ETA/KB/retrieval claims.

## Planning

```text
python helpers/blob_source.py --plan intent.json
```

UTF-8 intent:

```json
{"schema_version":"1.0","endpoint":"https://svc.search.windows.net","name":"manuals","owner":"owner@example.com","storage_id":"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/Example/providers/Microsoft.Storage/storageAccounts/example","container":"documents","prefix":"Reports/","is_adls":false,"api_version":"2026-04-01","processing":"minimal-lexical","network_access":"public","identity":"system-assigned","permission_options":[],"ingestion_schedule":null,"description":null,"rbac":{"assignments":[{"id":"<observed-assignment>","principalId":"<observed-principal>"}]},"network":{"posture":"public","evidence":"<fresh-readback-reference>"},"inventory_limits":{"max_pages":100,"max_objects":10000,"max_requests":25000,"deadline_seconds":600},"poll":{"deadline_seconds":600,"max_requests":120,"interval_seconds":5}}
```

Content fit (no default): `minimal-lexical`=minimal/no vectors,
`minimal-vector`=minimal/[vectors](vector-contracts.md),
`standard-cu`=standard/optional vectors; not KB reasoning.
Public/system-assigned; no schedules/permission ingestion.
Blob: `2026-04-01` or `2026-08-01-preview`; ADLS: preview, `is_adls: true`,
directory prefix without trailing `/`. Root: explicit `prefix: ""`, no widening.
Description: text/null; other modes: `planning-processing-unsupported`.

No writes, role/policy/auth changes, installs/polling/cleanup. Before approval,
verify requirements/access/security/cost/data; references alone aren't verification.

Two exact Search GETs bracket complete two-pass Storage observation. Reuse
requires matching definition/ETag, Storage binding and four generated identities.
`reuse_input_file`/`reuse_result_file`: retained approved input/successful creation
result. Validate pairing/types before auth; load only for redacted binding.
Required fingerprints/boundaries/source ETags/definitions/generated identities
must match fresh readback. Unproven binding: `source-binding-unverified`.
Old consent/readiness never authorizes new work.

Exit `0`: `status: planned`, `plan_fingerprint`, `execution_input`,
`approval_summary`, request IDs and `writes_performed: []`. Save only
`execution_input`; its approval is false and the executor rejects it until
actual unchanged-plan approval. Private artifacts preserve ResourceId connection
strings/fingerprints; ordinary result redaction is unchanged.
Summaries omit object/receipt paths, raw ACLs/integrity values.
No ingestion/retrieval readiness. Fresh exact reuse sets `execution_required` and
`mutation_approval_required` false: no executor or approval needed.
Drift: rerun `--plan`, replace the artifact, discard consent; never hand-edit
nested plans/hashes. Cleanup stays separate and run-owned-only.

For `standard-cu`, read [CU choices/wire](blob-cu-contracts.md).
`content_understanding` binds CU; optional `embedding` selects source vectors.

## Discovery

`python helpers/blob_source.py --discover <boundary.json>` accepts this closed
JSON (no approval):

```json
{"boundary":{"storage_id":"<ARM-account-ID>","container":"<container-or-filesystem>","prefix":"Reports/","is_adls":false},"inventory_limits":{"max_pages":100,"max_objects":10000,"max_requests":25000,"deadline_seconds":600}}
```

Arbitrary partial-name prefixes: `boundary-ambiguous`.
Public cloud/private DNS.

Read all pages twice including empty continuations. Exit `0` returns
`status: discovered`, `mutation: none`, `writes_performed: []`, boundary/account,
sorted objects (URL/path/size/ETag/version), ADLS path/property digests,
request IDs, `inventory_digest`; not approval/ingestion.
Incomplete/duplicate/out-of-scope/unreadable/unstable evidence blocks.
ADLS HEADs path/ancestor ACLs; no raw ACL/content. Operator access is not Search access.
Every path has an ACL HEAD; every non-root path also has a properties HEAD for
type and matching ETag. Root has no type header. Preserve ancestors and normalize
quoted/unquoted Blob/DFS ETags only for comparison; never skip required reads.

Inventory bounds apply per discovery: pages/objects per pass; requests/time
across both passes, including empty pages and all HEADs. Maximum accepted limits
are 1000 pages, 100000 objects, 200000 requests and 3600 seconds; exceeding any
bound blocks, never truncates. Planning adds at most two Search GETs and shares
its time budget with discovery. Bodies are capped at 8 MiB plus one overflow
probe byte. Socket watchdog interrupts body reads; DNS/connect/header
acquisition and scheduling are not hard wall-clock bounded. Redirects and
unsupported deadline readers block. Limits are safety bounds, not spending consent.

## Apply

`python helpers/blob_source.py --input <approved.json>` uses:

```json
{"schema_version":"1.0","plan":{},"approval":{"confirmed":true,"fingerprint":"sha256:<canonical-plan-digest>"}}
```

Canonical JSON: UTF-8, sorted keys, ASCII-escaped/compact.
`operation: reconcile-and-monitor`, `owner`,
`cleanup_approved: false`, discovered `boundary`, `inventory_digest`,
`inventory_limits`, `source`,
`poll: {"deadline_seconds":600,"max_requests":120,"interval_seconds":5}`.
Planner reuse: `expected_generated`, four typed/name/service-managed identities,
checked before writes; legacy artifacts remain valid.
Planner creation sets `expected_source_absent: true`; an intervening source
blocks. Redacted creation readback must match an acknowledged PUT ETag;
ambiguous unproven ownership remains partial, never adopted or cleaned up.

`source`: `operation: reconcile`, `resource_type:
knowledge-source`, exact `endpoint`/`name`/`api_version`, `action: create`
or `reuse`, matching `owner`, `cleanup_approved: false`, approved
`desired`, and `source_evidence` with `verified: true` and the same
`inventory_digest`. ADLS also requires `path_verified: true`, `acl_verified:
true` attest metadata, not effective Search permissions.

`desired`: matching `name`, `kind: azureBlob`; `azureBlobParameters`:
`connectionString: ResourceId=<exact-storage-resource-id>`, `containerName`,
exact `folderPath` (`null` for explicit root), boolean `isADLSGen2`,
`ingestionParameters`. Optional [shared controls](contracts.md).
No keys/SAS/updates/credential environments or supplied `createdResources`/`assetStore`.

Recompute approval/evidence; block drift. Create conditionally/reuse zero-write;
supplied ETag must match.
Poll GET `knowledgesources('{name}')/status` within bounds.
Only 408/429/500/502/503/504/transport-ambiguous reads retry; 403/404 block.

Require completed start/end times at or after the pre-write cutoff,
nonnegative integer `itemsUpdatesProcessed`, `itemsUpdatesFailed`, and
`itemsSkipped`, zero failures, no observed relevant errors or active cycle.
Missing counts are not zero.
Completed `status` may be absent; reject `partialSuccess`/`failure`/malformed/unknown.
Never trigger indexers/edit schedules; stale success cannot pass.
Reuse also excludes the first observed completion.

## Results

All new modes use `--receipt-dir`; reuse readiness uses read-only `--capture`:
[checkpoint/recheck](../references/blob-readiness-recheck.md). No reconstructed cutoffs.

Recheck inventory/definition/ETag/generated identities.
Exit `0`: `completed`; unverified zero-write reuse is exit `2`,
`blocked` with `reconciliation: completed`. After a write, exit `3` / `partial`
retains approval, first failure, and `resources_remaining.run_owned`.
Conflicting children aren't owned. Return `source.generated`,
`readiness`/digest/warnings/cleanup; errors retain status/request ID/digest,
not sensitive text. No rollback/source writes/child edits.

Owner handles RBAC/private links. CLI Entra: ARM/Storage/Search audiences.
Probes: ARM GET `2025-06-01`, Storage `2025-05-05` listing,
ADLS HEAD `action=getAccessControl&upn=false`.
