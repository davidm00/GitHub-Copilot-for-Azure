# Shared CU ingestion contract

Use for CU-backed ingestion. Current adapters support Standard File and Blob/ADLS.
This contract owns shared CU dependencies, necessary checks, costs and pending
plans; adapters retain only source-specific wire/auth and ingestion lifecycle.
It does not enable CU for unsupported connectors.
Use Azure AI Services directly; no project, agent, external setup skill or `azd`
dependency. Use native resource reads, not agent-tool discovery or general AI-app setup.

## Independent dependencies

Show each selected dependency, its purpose, endpoint/deployment, access and cost
in the proposed plan. Shared accounts do not merge these choices:

| Dependency | Selected when | Purpose and boundary |
|---|---|---|
| Content Understanding | Standard extraction | Extract/process documents through an `AIServices` account; CU processing charges apply. It does not select source vectors or KB reasoning. |
| Source embedding model | Hybrid/vector search selected | Create source vectors, with embedding processing/data movement and vector storage costs. `text-embedding-3-small` is an embedding model, not an extractor or chat model. |
| KB chat model | Reasoning or answer synthesis selected | KB query reasoning/answer generation; separate model/access/cost choice. A source embedding deployment does not satisfy this dependency. |

The source helpers disable image verbalization and do not configure source chat.
Require only models the selected CU operation uses; a CU deployment prerequisite
does not enable Search `embeddingModel`. Never add CU because hybrid was chosen,
add source vectors because CU was chosen, or require KB chat merely for ingestion.
Preserve existing selections; changing any dependency needs concrete approval.

## Necessary checks, not extra configuration

Reuse fresh exact readbacks; do not repeat completed discovery or ask whether
the account is "configured." No defaults-setup confirmation or direct CU analysis
probe is required. Processing success is verified by the approved ingestion,
not by a new billable preflight.

The File planner checks the exact selected account using ARM GET
`https://management.azure.com<cu-resource-id>?api-version=2024-10-01`.
For a missing readback, use `az rest --method get --url <exact-url>`.
Confirm matching resource ID, `kind: AIServices`,
`properties.provisioningState: Succeeded`, observed endpoint/location and the
selected path's access/network requirements. File's approved ENV-key path needs
`properties.disableLocalAuth: false`; never fetch or print the key.
Use published CU region support for the selected operation, not name similarity.

Blob uses Search's existing system identity and Cognitive Services User on the
AI Services account, not File's key channel. Use exact identity/role readbacks
through [native role checks](bootstrap-azure.md#roles-readiness-and-return).
Only selected source embeddings use the separate
[embedding checks](../helpers/vector-contracts.md#supported-choices).
`prerequisites.configuration` refers to these selected processing/deployment
facts, not additional account settings or a certificate of successful processing.

Metadata/readiness is not effective-access or ingestion proof. Explain concrete
risks: a disabled File key channel prevents authentication; a missing required
deployment prevents its model call; a denied network path prevents service access.
Do not invent missing analyzers/defaults from absent generic evidence.
Actual service failures retain their original status/request ID and ownership.

## Keep a useful draft when one dependency is pending

Present "Draft ready; one dependency check remains," not a capability rejection.
Use this workflow-summary shape, not a helper execution envelope:

```json
{"planning_status":"blocked_pending_dependency","execution_input":null,"resolved_choices_ref":"<retained private intent/readbacks>","remaining_checks":[{"target":"<exact selected dependency>","action":"<necessary GET or owner action>","success_criteria":"<specific required fields/access>","reason":"<actual execution risk>"}],"next_step":"Complete only the remaining checks, then resume planning."}
```

Retain resolved source/KB names, boundaries, processing/model choices, caller,
owner, readbacks and prior approval references privately. Do not rediscover or
re-question unchanged choices. List only genuinely unresolved checks; a missing
generic configuration attestation does not establish a missing dependency.
If an actual check fails, preserve the exact failure alongside this draft.
Keep earlier completed writes/ownership visible; the draft itself performs none.

Never pass this summary to `--input`, emit a fabricated executable plan, or seek
execution approval while a required dependency remains unresolved. Do not fill
future verification fields or transfer infrastructure consent to source/KB writes.
When resolved, resume the normal `--plan` with retained choices, refresh required
readbacks and approve only concrete new/materially changed actions. Preserve
valid approval for unchanged independent work. No silent extraction downgrade.

## Only missing resources need setup

Use [native ARM actions](bootstrap-azure.md#native-arm-actions), not agent tooling.
For CU, use account A's body with `kind: AIServices`, API `2024-10-01`.
Only approved File CU sets `disableLocalAuth: false`; Blob stays keyless.
Retain approved region/tags/network/cost/ownership and use native model/role actions
only when required. Obtain separate approval before any resource/access change;
verify returned IDs, endpoint, deployments and settings before resuming.

## Authorities

Authorities: failure/conflict/uncertainty only.

[CU account GET](https://learn.microsoft.com/rest/api/aiservices/accountmanagement/accounts/get?view=rest-aiservices-accountmanagement-2024-10-01),
[CU account PUT](https://learn.microsoft.com/rest/api/aiservices/accountmanagement/accounts/create?view=rest-aiservices-accountmanagement-2024-10-01),
[CU skill and supported regions](https://learn.microsoft.com/azure/search/cognitive-search-skill-content-understanding).
