# Create or reuse a Search service

## When to use

Create/ready-reuse Search for direct or File/Blob/KB requests.
Return service; no sources/KBs/agents here.

## Do not use

Not classic Search index/query/app work or administration.
Helper: Basic/Standard, public networking, disabled local auth, system-assigned
identity only. Other settings block; never
downgrade, enable keys, change shared resources or invent requirements.

## Inputs and discovery order

Execution checklist, not a questionnaire. Reuse prompt/session/workspace;
otherwise `az account show` supplies caller/tenant/default subscription.
Explicit scope wins; no silent `az account set`. Missing CLI/sign-in blocks;
account context is not access proof. Reads need no approval.
Recommend; one focused question if unresolved.

| Input | Why needed | Required? | Discovery order | Safe default | If missing or unanswered | Reconfirmation trigger |
|---|---|---|---|---|---|---|
| Scope/group/region | Target | Before plan | CLI/IDs | Propose existing | Offer choices | Scope |
| Service/action | Intent | Before plan | Exact Azure GET | Recommend reuse | Reuse/new/another | Action/ID |
| Capacity/auth/network/cost | Cost/access | Before write | Readback/prices | Propose/preserve | Concrete settings | Settings |
| Owner/tags/requirements | Ownership | Before write | Context/evidence | No assumptions | Confirm missing | Requirements |
| Receipts/limits | Execution | Before plan | Supported options | Bounded/private | Propose | Location/limits |

## Decisions

Honor explicit reuse/new intent; never repeat resolved choices. Read supplied IDs first.
Name/endpoint/choice intake: [resource intake](../references/resource-intake.md).
Only unresolved selection lists candidates: known group uses `az search service list --resource-group <group>
--subscription <sub>`; otherwise browse only Search services in the selected subscription.
Read every page in that scope, never unrelated resource types/subscriptions.
Offer "Reuse <name> (recommended), create new, or choose another."
Offer observed choices + freeform names/endpoints; resolve IDs, never demand them.
Unresolved intent needs a choice even for one candidate;
multiple compatible services require exact-ID selection behind displayed names.
No match in a narrower scope is not subscription-wide absence.
Unreadable/denied is unknown, not absent. New intent requires exact-name absence;
existing/conflicting state is not permission to overwrite or suffix-create.

New group choice: `az group list --subscription <sub>` (metadata only).
Propose task-derived name/group/owner and supported region near data, respecting
residency. Small public-network trial: recommend Basic, one replica/partition,
subject to price/quota/requirements; offer Standard for scale. Not a production
SLA or automatic capacity choice. Preserve required posture; unsupported needs
block/handoff, never downgrade. Gather evidence before approval.

Planning requires an **existing ready resource group**.
If absent, use [resource-group-only prerequisite](../references/bootstrap-azure.md#resource-group-only-prerequisite):
approve RG-only, verify readiness, then resume.
No Search/model/role/Storage/CU dispatch or unknown-body approval.

Unresolved region: `--regions scope.json`; present canonical `available_locations`
for selection. Freeform answers need Search-specific `--plan` validation before approval.
New Search: `az search usage list --location <region> --subscription <sub>`;
quota is not capacity. Resolve prices/region/requirements.
Ready reuse skips setup/catalog discovery;
requires no embeddings, chat, CU or Storage provisioning.

## Proposed plan

Read [bootstrap helper contract](../helpers/bootstrap-contracts.md):
schema 2.0 choices/example, private storage and CLI limits.
Do not author nested execution envelopes; hashes stay internal.
New locations fold ASCII case/whitespace (`East US` to `eastus`), not availability
proof; retained artifacts stay unchanged.
For creation, reuse a valid unexpired artifact for unchanged choices.
Otherwise plan; reuse intent always needs fresh readbacks.
Use an absolute helper path:

```text
python "<skill-root>/helpers/bootstrap_azure.py" --plan choices.json
```

Choose `action: create` or `action: reuse`. Planning reads Azure, writes private
unapproved `<artifact_id>.plan.json`, and returns an approval summary; no Azure writes.
Verified reuse: `execution_required: false`, `mutation_approval_required: false`;
return without an apply step or mutation consent.

## Confirmation

Creation disclosure: exact target/group/region, SKU/capacity/cost, network/auth,
system identity, tags/owner, limits, intended write and retained resources.
Obtain actual consent before the write; silence or a stored approval flag is not consent.
One approval covers concrete unchanged Search changes. Reuse valid consolidated
bootstrap approval for this exact retained Search artifact without another question;
do not regenerate it merely to enter this procedure.
Never extend that approval to unknown future bodies, source/KB writes or cleanup.
Material target/cost/access/identity/operation drift invalidates it; harmless
server metadata, supported defaults, ordering or casing does not renew consent.

## Mutation

After approval:

```text
python "<skill-root>/helpers/bootstrap_azure.py" --apply "<private-directory>/<artifact_id>.plan.json" --approve
```

Helper revalidates artifact/context/supported region/fresh exact-name absence, then one approved
`az rest` PUT (`2025-05-01`, body-file `@`).
No write retry/deletion/role assignment.
GET/PUT is not atomic: exclusive new-name authority is required.
Expired/used/changed artifacts need fresh planning, not manual envelope edits.

## Verification

Native `az resource wait` uses the same API, then an authoritative raw GET
establishes selected target and required material settings. Matching precedes
ownership/readiness claims. Require provisioning succeeded, status running,
endpoint and system identity/principal/tenant readback; existence/acceptance is not ready.
Wait failure remains primary even if the final GET is ready.
CLI timeout/cleanup: best-effort; rejection is post-capture, not a memory
or hard end-to-end bound. No custom polling framework.

ARM readiness is **not** Search data-plane authorization, role propagation,
source ingestion, vector verification or KB grounded retrieval. Caller checks remain required.

## Failure and partial completion

Preserve first code/status/request ID, attempted writes and private receipt ID.
Return blocked before writes, or partial after uncertain/completed writes; retain
run-owned versus unverified resources. Never claim ownership from matching names alone.
Only policy-implicated creation failure loads
[policy diagnostics](../references/search-substrate.md#azure-policy-diagnostics-after-creation-failure);
no preflight policy audit. Secondary diagnosis cannot replace the original failure,
authorize changes or turn unknown into compliance. Reconcile uncertainty read-only.

## Cleanup

Cleanup is unapproved and separate. The helper does not execute it.
Preserve shared/reused resources. If requested, hand off
[native cleanup](../references/bootstrap-azure.md#cleanup)
with retained operation evidence, fresh exclusive ownership/configuration,
children/scoped roles and separate approval. Never delete a service still used
by sources/KBs or unrelated workloads; never equate a failed command with absence.

## Return contract

Return helper `planned`, fresh `reused`, applied `completed`, `blocked`/`partial`,
available artifact/receipt and resource IDs.
Return observed endpoint/verified settings; planning isn't readiness.
Preserve writes and ownership/remaining-resource evidence.
Keep paths/raw errors/hashes private. ARM-only success is not
data-plane/ingestion/retrieval proof.
Resume the original caller with observed dependencies, not new KS/KB calls.

## References

Helper contract required; other links conditional.
