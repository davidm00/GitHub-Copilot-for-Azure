# Standard File dependency branch

Standard extraction, not minimal parsing, selects this branch. Provisioning an
account alone never proves Content Understanding readiness.

Read exact CU-capable `AIServices` endpoints from ARM; never derive them from OpenAI URLs.
Read [shared CU ingestion](cu-ingestion.md) for necessary checks, independent
model purposes and non-executable pending-dependency drafts.
Existing CU/deployment/access evidence permits planning; no setup-owner or `azd` prerequisite.
Do not ask for a separate account-configuration confirmation.
`prerequisites.configuration`: selected processing/required deployment evidence,
not a default-model setup certificate.
Only missing dependencies need native Azure setup; obtain separate approval.
`bootstrap-cu-contract-unresolved`: unresolved required dependency,
not for reuse. Never default to reduced extraction.

File standard binds `aiServices.uri` independently of optional source embeddings.
This planner disables image verbalization; source chat is not configured.

The documented key path requires explicit consent to local auth on the CU
resource only. Use the helper's approved `ai_services_api_key_environment`,
populated out of band. Never put keys in chat, plans, logs or command arguments;
never use Search/Storage keys. Policy prohibiting this supported path blocks.

## Standard File planning

In the ordinary File request set `extraction_mode: "standard"` and add this
closed `content_understanding` choice; all fields required:

```json
{"endpoint":"https://cu.services.ai.azure.com","resource_id":"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.CognitiveServices/accounts/cu","auth":"api-key-environment","api_key_environment":"CU_API_KEY","prerequisites":{"resource":"<CU capability/region readback>","configuration":"<selected processing/required deployment evidence>","identity":"<explicit local-auth/access evidence>","network":"<effective reachability evidence>"}}
```

Evidence references are 1–4096 characters; private artifact only, not summaries.
Use observed endpoints, never guessed URLs. `vectorization: "none"` omits
`embeddingModel`; `azureOpenAI` needs independent
[embedding choices](../helpers/vector-contracts.md). Endpoints need not match.
Minimal omits CU choices. Neither filename nor MIME selects extraction.

`file_source.py --plan` GETs the exact ARM account (`2024-10-01`) before and
after Search discovery. It requires `AIServices`, ready provisioning, matching
endpoint/location and explicit `disableLocalAuth: false`/network posture.
The helper never enables local auth or fetches keys. ARM proves account metadata,
not processing success, key validity or effective access. Verify applicable
evidence before source approval; user yes/no answers are not readback proof.

New artifacts bind `file_cu_plan_version: "1.0"`, CU choices, optional embeddings,
ENV reference and selected `cu_resource_state` to the internal fingerprint.
Execution refreshes ARM before writes; endpoint/auth/network/identity drift blocks.
Tags and unrelated account metadata do not invalidate approval.
Location compares ASCII case/whitespace only (`East US`/`eastus`), not region
guesses or availability. Equivalent readbacks need no new approval; real region
drift blocks. Other fields stay strict; retained snapshots/fingerprints are unchanged.
Legacy complete-wire artifacts remain byte/fingerprint compatible.
Only the existing executor injects the ENV value into the source PUT, in memory.

Review billable CU (no daily free document allowance), content moving from Search
to CU/selected embeddings, possible cross-region processing, retention and auth.
No CU/model/Storage provisioning or KB changes are included.
Exact source/ETag/file-marker reuse needs no mutation approval or ENV value;
readbacks do not prove CU processing or retrieval. Existing upload verification,
first-failure/partial ownership and separately approved cleanup still apply.

## Source settings: API versus helper

The table distinguishes API requirements from helper choices.
File standard: `2026-08-01-preview`. Blob CU: GA `2026-04-01` or
August preview. ADLS preview is this helper's boundary.

| Setting | Public contract | Helper boundary |
| --- | --- | --- |
| Name/type | `name`, `kind`, source parameters required | Stable name; owner/purpose are workflow inputs |
| Description | Optional text | Do not demand it; Blob accepts null |
| Location | File uses Search-managed storage; Blob requires `connectionString`/`containerName` | Selected local files versus existing Storage/container; no File Storage provisioning |
| Prefix | Blob `folderPath` optional/null | Explicit `prefix: ""` root consent is helper safety |
| Extraction | Optional `contentExtractionMode`, default `minimal`; CU opt-in `standard` | Planners require an explicit choice; API default is not content-fit guidance |
| Embeddings | Optional/nullable `embeddingModel` | Off by default; independently selected deployment/auth |
| Source chat | Optional `chatCompletionModel` for image verbalization/context extraction | Planners disable verbalization; CU does not require KB chat |
| Auth | Caller/dependency access required; Blob can use keys or ResourceId/MI | Search/Storage keyless; Blob keys/SAS unsupported here; File CU uses approved ENV key |
| Advanced | Blob schedule optional; permission/private ingestion are conditional preview options | Blob planner public/system-assigned, no schedule/permissions. File has no indexer/schedule, rejects `networkAccessMode` |

Helper-required null/false/empty fields do not make optional API settings mandatory
questions. Portal API-key selections do not change intentional helper auth defaults.

Blob's documented CU embedding-deployment prerequisite is not Search
`embeddingModel`. File standard refers to CU skill prerequisites.
Default mappings need contract/error evidence; never invent them.

For detected types, tier/size/count limits and May service versus August helper
support, use [source formats/API choices](platform-interfaces.md#source-formats).
Hints do not override server detection or establish answer suitability.
Preserve binary bytes; never execute
scripts. Actual images need August standard; server 415 stops, retaining prior
writes and ownership. No local admission classifier, suffix gate or automatic mode
switch; authorized sample inspection informs suitability, not service admission.

File prose requires `fileParameters.ingestionParameters` even though Swagger
doesn't mark it required. Source-specific docs override generic schema inference.

## Authorities

Authorities: failure/conflict/uncertainty only.

[CU setup](https://learn.microsoft.com/azure/ai-services/content-understanding/quickstart/use-rest-api),
[File standard contract](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-file#configure-standard-extraction),
[File documentation](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-file),
[Blob documentation](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-blob),
[August ingestion parameters](https://learn.microsoft.com/en-us/rest/api/searchservice/knowledge-sources/create-or-update?view=rest-searchservice-2026-08-01-preview&preserve-view=true),
[CU account GET](https://learn.microsoft.com/en-us/rest/api/aiservices/accountmanagement/accounts/get?view=rest-aiservices-accountmanagement-2024-10-01),
[GA schema](https://github.com/Azure/azure-rest-api-specs/blob/main/specification/search/data-plane/Search/stable/2026-04-01/search.json),
[preview schema](https://github.com/Azure/azure-rest-api-specs/blob/main/specification/search/data-plane/Search/preview/2026-08-01-preview/search.json).
