# Create a knowledge base

## When to use

Create exactly one KB over one verified File, Blob or ADLS Gen2 source.
Single-source helper; Azure supports multiple sources.

## Do not use

Not multiple sources, unsupported connectors, classic Search or agents.
Never mutate conflicts, select duplicates or call GA extraction synthesis.

## Inputs and discovery order

Resolve prompt/session/workspace/exact Azure readback, safe default, then one
focused question. Label sources; silence is not approval. Reads need no approval.

| Input | Why needed | Required? | Discovery order | Safe default | If missing or unanswered | Reconfirmation trigger |
|---|---|---|---|---|---|---|
| Tenant/subscription; group/name/region | Scope | Required | Azure context/selection | Propose absent group | Ask ambiguity | Scope change |
| Search ID/endpoint | Target | Output before source creation | Discovery/bootstrap readback | Honor reuse/new choice | Bootstrap absent | Target change |
| Source ID/type/boundary/definition | Grounding | Before approval | Source readback | None | Create absent; block unverified | Source |
| Base name/owner/purpose | Stable identity | Required | Prompt, session, exact-name readback | Deterministic after owner/purpose | Block | Identity/owner change |
| Outcome/API/mode | Response | Required | Prompt/readback | GA Blob: minimal/extractive | Block unsupported | Outcome/API |
| Effort/model/version/capacity | Preview | Conditional | Choice/bootstrap | Minimal/extractive; honor explicit choice | Resolve dependencies | Model/capacity/region |
| Caller/roles | Retrieval | Before retrieval | Discovery/bootstrap | Service-scoped reader | Plan missing roles | Identity/scope |
| Network/permission mode | Security | Required | Source/Search readback | Preserve posture | Block | Network or permission posture changed |
| Acceptance/source identity | Citation proof | Required | Prompt, source inventory | None | Block | Question/identity change |
| Unrelated question | No-evidence proof | Required | Prompt | None | Block | Question change |
| Cleanup owner | Recovery | Required | Prompt, session | Cleanup not approved | Block | Owner change |

## Decisions

### Required versus optional settings

Preview requires `name` and `knowledgeSources`; description is optional.
Owner/purpose: workflow metadata, not API requirements.
API-optional output/effort are explicit here: default new KBs to minimal/extractive.
Minimal extractive KB adds no model. `minimal` requires `extractiveData`; no synthesis.
Low/medium or synthesis requires a KB model; source CU/embeddings alone do not.
Omitted KB/request effort defaults to `low`, not the portal's Minimal selection.
Retrieval/answer instructions are optional and preview-only.
API `auto` is outside this helper's minimal/low/medium scope; hand off explicitly.

For low/medium or synthesis, reuse a supplied chat deployment or ask which to use.
If none exists, [shared bootstrap](../references/search-substrate.md) proposes
supported model/version/region/capacity/cost/access and deploys only after approval.
Verify readiness/access, then resume KB creation; never silently downgrade.
Resolve missing/unverified Search via its [owner](../search-services/create.md);
other missing infrastructure stays shared, without routine policy reads.

Retain source IDs/API/boundary/definition, ownership/health/permissions/reuse proof
and content assessment/uncertainty, answer needs and ingestion mode through
prerequisites; resume KB plus validated retrieval, not source-only.
Refresh readback; material mismatch blocks.
Only then present the KB plan; never preapprove a future `verified_source`
or reuse bootstrap consent for KB mutation.

GET exact name; paginate candidates only if unresolved. One normalized match:
zero-write; multiple compatible KBs require exact-ID selection.
Same-name conflict/inaccessible blocks.
Choose:

- `minimal`: direct extractive grounding. Blob-only, non-agentic,
  non-permission-preview work defaults to GA `2026-04-01`, with no preview-only
  fields or synthesized `I don't know`.
- Preview minimal: `outputMode: extractiveData` and
  `retrievalReasoningEffort: {kind: minimal}`.
- Low/medium: one preflighted chat model; `extractiveData` or `answerSynthesis`.
  Low is one-pass; medium may follow up. Preserve a low miss and ask one tradeoff
  question; never auto-escalate.

File, synthesis, agent connection, permission-aware behavior and low/medium
require preview and explicit approval.

### Agent-compatible minimal transition

Read the existing GA minimal KB through `2026-08-01-preview`; verify its source.
With separate approval, use `action: update` and the current ETag to set only
`outputMode: extractiveData` and `retrievalReasoningEffort: {kind: minimal}`.
Leave models, source contents, RBAC and networking unchanged;
preserve unrelated fields; never overwrite conflicts.
Read back and verify agent MCP retrieval before zero-write reuse.
GA retrieval is not MCP proof.

## Proposed plan

Read [helper contracts](../helpers/contracts.md) before planning.
Show IDs/source, owner/API/mode/model, data movement, access/cost, acceptance,
actions, verification and cleanup/retained resources. No write.

## Confirmation

Keep immutable proposed mutation plan/`plan_fingerprint`, `cleanup_approved: false`.
Approve concrete changes once.
Changed source/mode/model/boundary/access, acceptance or freshness requires review;
never ask users to calculate or repeat hashes.

## Mutation

After approval, invoke:

```text
python helpers/search_reconcile.py --input <approved-envelope.json>
```

`reconcile`/`knowledge-base` binds endpoint/name/API/definition/owner,
`cleanup_approved: false`, verified source name/normalized same-API digest.
Before create/update/reuse, a fresh source GET must match.
Block absent/unreadable/drift, mode/API mixing and extra sources.
Conditional create/ETag-update reads back. Exit `2`: blocked/no-write;
`3`: partial.

GA omits preview fields; preview uses selected settings. Reuse roles/dependencies. Never update conflicts,
add sources, resize models, broaden access or modify source/generated children.
Resolve ambiguity on the same identity.

## Verification

Verify owner, source identity, API/mode/model and keyless access/roles/network.
Use REST [Retrieve](retrieve.md), without MCP.
Require original File path plus file ID or Blob/ADLS URL/path plus ETag/version
citations; a bare path/URL is insufficient.
For unrelated questions, `answerSynthesis` requires semantic abstention per the
[abstention criteria](retrieve.md#verification) and any explicit exact-output contract.
GA/preview `extractiveData` requires no supporting extracts.
Recheck stable IDs/zero writes.
Optional: [Connect](../agents/connect.md).

## Failure and partial completion

Preserve first status/message/request ID. Low failure never authorizes medium.
Citation/access/model/region/definition/source mismatch blocks.
`blocked`: evidence, no writes, next decision.
`partial`: writes, unverified state, ownership and separately approved cleanup.

## Cleanup

Creation excludes cleanup. A separate cleanup plan and approval deletes the
run-owned base before exclusive run-owned dependencies. Retain reused resources,
source content, retained sources' generated children and shared roles.
Unclear ownership blocks. Use `operation: delete` with the owned definition
digest and current ETag.

## Return contract

Return status/IDs/API/mode/model, access/data movement, verification,
first failure/warnings/ownership/cleanup; keep digests internal.

## References

- [Audit fields](../references/platform-contracts.md).
- [Interface versions](../references/platform-interfaces.md).

Authorities: failure/conflict/uncertainty only.

- [Preview](https://learn.microsoft.com/rest/api/searchservice/knowledge-bases/create-or-update?view=rest-searchservice-2026-08-01-preview)
- [Reasoning/models](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
