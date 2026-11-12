# Plan and apply

## Quick starts

- "Check whether this machine is ready to build a Topic Graph."
- "Inspect the source index `<index>` and plan a Topic Graph build; show me the approval card."
- "Apply the approved plan and verify the new generation."

## Use this path

Use this path to go from a Search source index with stored chunk vectors to a verified, unpublished `topicgraph-*` topic index.

## Preflight

1. Follow [runtime setup](../../graph-guide/references/install-and-checks.md#plugin-and-clis): explicit `setup topicgraph`, then `run topicgraph topic-graph-build --help`. Retain the `run <domain>` launcher; warm run never installs.
   Topic generation also requires the [native binary](native-runtime.md).
2. Global flags go **before** the verb and repeat unchanged on every command. Fill placeholders, nothing else (`<search>` is the service name, not a URL; `<tenant>` from `az account show --query tenantId -o tsv`):

   ```bash
   topic-graph-build --state-dir <absolute-state> --tenant-id <tenant> --subscription-id <sub> --resource-group <rg> --search-service <search> --source-index <index> --json doctor
   ```

   Doctor only reads. Follow the first `fail` check's `next_step`; `warn` does not block. Do not probe flags with trial runs; on an error, fix only the flag it names.
3. Topics are named by a chat deployment. With an Entity Graph connect file, put `--build-args <file>` before the verb: it fills tenant, subscription, resource group, Search service, embedding model and chat deployment, so skip discovery and ask nothing. Otherwise offer the signed-in subscription by name (`az account show`); list subscriptions with `bootstrap.py run entity entity-graph-provision discover --tenant-id <tenant>` only if the user wants another. Run `discover --tenant-id <tenant> --subscription-id <sub>`, show its table and ask for a chat model by name (never default, guess or narrow scope). Run `discover --tenant-id <tenant> --subscription-id <sub> --row <N> --discovery-id <id> --role chat`; pass `args.topicgraph_doctor` to `doctor` and `args.topicgraph_plan` to `plan`. Doctor reads ARM capabilities only; no completion, no spend.

## Inspect and plan

1. Tell the operator the tenant, subscription, resource group, and Search service, then run `inspect` and `plan` with the global source flags before the verb (for a managed graph content index `*-managed-*-index`, use `--key-field uid --text-field snippet --source-field blob_url --vector-field snippet_vector`, and `--embedding-model-id` is read from the Entity Graph connect binding for that Search service when omitted).

   ```bash
   topic-graph-build --state-dir <absolute-state> --tenant-id <tenant> --subscription-id <sub> --resource-group <rg> --search-service <search> --source-index <index> --dataset <slug> --key-field <key> --text-field <text> --source-field <source> --vector-field <vector> --embedding-model-id <model> --json inspect
   topic-graph-build --state-dir <absolute-state> --tenant-id <tenant> --subscription-id <sub> --resource-group <rg> --search-service <search> --source-index <index> --dataset <slug> --key-field <key> --text-field <text> --source-field <source> --vector-field <vector> --embedding-model-id <model> --json plan --model-endpoint <https-endpoint> --model-deployment <chat> --model-name <model-name>
   ```

2. `plan` requires the `args.topicgraph_plan` flags (`--model-endpoint`, `--model-deployment`, `--model-name`) after the verb. `--model-call-cap <n>` lowers or raises the most naming calls the build tool may make (default about ten per expected leaf topic, at least 50); `--model-api-version` overrides the default API version. Model settings and the cap are part of the plan ID.
3. Before the card say one plain line, such as "This reads your index, names about 40 topics with gpt-5.4-mini, and makes a new topic index." Then show the card verbatim: a headline, three bullets, time and cost. Its `details` (download, sign-in, scoring profile) are shown only when asked.
4. Optional global flag: `--title-field <field>` gives the naming model document titles as evidence. Leaf topics hold at most 100 chunks, the largest size the build tool allows.
5. Use `--reader` or `--drop-reader` after `plan` only when the operator names a principal. If you re-plan, show the new card and ask again.

A verified managed graph content index (`*-managed-*-index`) whose Knowledge Source synchronization completed (`status=success`), with no indexer run or `entity-graph-build update` in flight, is already frozen for Topic Graph; never ask the user for separate producer-freeze evidence or pause the managed indexer.

Topic Graph reads the source index in place with no copy. The physical key must be a retrievable string (`filterable` and `sortable` are not required, and there is no document-count cap). The vector field must be `Collection(Edm.Single)` with `stored: true`, `retrievable: true` and an HNSW profile using `cosine` or `dotProduct`; `scalarQuantization` and `binaryQuantization` compression work in place. Otherwise planning stops with `NATIVE_SOURCE_INCOMPATIBLE`, `SOURCE_VECTORS_NOT_STORED` or `SOURCE_VECTORS_NOT_RETRIEVABLE`; ask the source owner for a compatible source. Never edit or copy a managed index yourself.

Unknown, malformed or exhausted Search quotas block planning. Serverless services need finite per-index storage and vector limits and a free index slot; their cards itemize model naming separately from unknown billable Serverless compute and storage. The card never prices model calls; it states the most calls the build tool may make.

## Apply and verify

1. Run `apply` and `verify` directly in the main session shell (`initial_wait: 600`), never inside a subagent (backgrounded subagent shells do not notify the parent session). After the user approves:

   ```bash
   topic-graph-build --state-dir <absolute-state> apply --plan-id <plan-id> --confirm-writes
   ```

   Run the `apply_command` that `plan` printed, verbatim; never retype `--state-dir`. The saved plan holds every other setting. On `PLAN_NOT_FOUND`, tell the user in one plain line and run the command its next step names; doctor doesn't list plans.
2. Do not pass `--model-*` or `--reader` flags to `apply`; the plan holds them. On `PLAN_BOUND_FLAG`, drop them and rerun.
3. `apply` runs the TopicGraph executable against the source index, then uploads the topic release into the new index. On `MODEL_CALL_BUDGET_EXHAUSTED`, re-plan with a higher `--model-call-cap`, show the new card, and apply after approval; the build resumes where it stopped.
4. Run `topic-graph-build --state-dir <absolute-state> --json verify` right after `apply` succeeds. It reads every document back and returns the publish approval card. Stop there; publishing is a separate path.

`verify` also reports `topicgraph_output.directory`: the build's output folder, kept under `<absolute-state>/topicgraph-output/`. Pass that value unchanged to `ontology-build connect --topic-graph-output`; keep the folder if the operator wants an ontology.

Uploads are bounded by document count and a 15 MiB complete JSON request budget.
`PUBLICATION_DOCUMENT_TOO_LARGE` requires reducing the named document payload, not retrying it.
After a partial upload failure, use reconcile; confirmed sub-batches are not rolled back or blindly retried.

## Return

Report the phase, exact plan ID, target index, whether the result is planned, applied, or verified, the output folder, and the single safe next action. Never claim a plan proves access, quota, or readiness to publish.
