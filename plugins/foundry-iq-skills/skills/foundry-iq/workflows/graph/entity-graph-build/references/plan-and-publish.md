# Plan and publish

## Quick starts

- "Build an Entity Graph from the documents in `<folder>`."
- "Plan the build with my OWL file and show the approval card."
- "Publish the verified generation."

## Use this path

Use this path to go from a document source and an existing Azure target to an approved plan, a verified generation, and a published descriptor.

## Preflight

1. Follow [runtime setup](../../graph-guide/references/install-and-checks.md#plugin-and-clis): explicit `setup entity`, then `run entity entity-graph-build --help`. Retain the `run <domain>` launcher; warm run never installs.
2. Run read-only `entity-graph-build doctor --json`, adding `--tenant-id`, `--build-journal`, and `--descriptor` when known.
3. The target comes only from a `ready` `entity-graph-provision connect` result: pass `--build-args <build_args_file>` (the saved `build_binding.build_args`); hand-write no target flag. Its `--embedding-model` is the model identity; a descriptor's `embedding_deployment` is a deployment name.

## Plan: run exactly

Fill placeholders only; paths are absolute and `<journal.json>` is a new file outside `<corpus>`. Run `fetch-sample` only for the built-in demo (`<corpus>` is `.\earnings-corpus`); otherwise start at `inventory` with the user's folder or Blob prefix. Put new `<manifest.json>` and `<journal.json>` files in `.\.entity\`, never a session folder, and reuse returned paths exactly.

Before `plan`, sample the documents (and any ontology) and draft `<description>`: 1-2 factual sentences on subject, document types and coverage; agents use it to pick this source. Style: "Chapter passages from Alexandre Dumas's The Count of Monte Cristo, covering Edmond Dantès's imprisonment, transformation, and pursuit of revenge; the lives and connections of the novel's characters; and themes of betrayal, loyalty, justice, wealth, and forgiveness."

```bash
entity-graph-build fetch-sample --output <corpus> --json
entity-graph-build inventory --source-kind local_path --source-reference <corpus> --output <manifest.json> --json
entity-graph-build plan --build-args <file> --source-kind local_path --source-reference <corpus> --source-manifest <manifest.json> --build-journal <journal.json> --ontology deferred --source-description "<description>" --json
```

`plan` accepts a missing target flag silently, so never drop one. On an error, fix only the flag it names.

1. Ontology: keep `--ontology deferred` (default): the Knowledge Source gets graph extraction with no ontology, so Search only chunks and embeds; attach the ontology later (see [Deferred ontology](deferred-ontology.md)). Setting an ontology here starts triple extraction at once, so do it only when the user already has the ontology they want: `--ontology inline_jsonld --ontology-path <ontology.jsonld>` (or `--ontology owl_file --ontology-path <ontology.jsonld>`) for the user's classes (offer a trial first), or `--ontology schema_org` when they explicitly ask for the built-in types now.
2. Every build has graph extraction and binds the Knowledge Base `entity-kb-<generation>` (`agentic_retrieval: true`); with `deferred`, the attach creates it.
3. For a customer Blob prefix (`--source-kind blob_prefix --source-reference https://<account>.blob.core.windows.net --source-resource-id <arm-id> --source-container <container> --source-prefix <prefix>`), `inventory` lists blobs without downloading them, and the Knowledge Source reads that container and prefix directly: no documents are copied to staging storage (only `local_path` and `zip_archive` are staged). If the prefix changes during indexing, `verify` checks completed indexer status and reports `source_drift`. Search drops deleted blobs only with [blob soft delete](https://learn.microsoft.com/en-us/azure/storage/blobs/soft-delete-blob-enable?tabs=azure-portal) on; have the owner enable it before deletions. `inspect`/`apply` warn `BLOB_SOFT_DELETE_OFF`/`_UNKNOWN`, never blocking. Targets may span subscriptions, use per-model OpenAI overrides (`--embedding-openai-*`, `--chat-openai-*`, `--kb-openai-*`, `--kb-chat-deployment`, `--kb-chat-model`) and Search's user-assigned or system-assigned identity (`--use-system-identity`). Model accounts come only from the user's choices in `entity-graph-provision discover`: a subscription from tier 1, then a row per role from tier 2 (repeat tier 2 for a role in another subscription), each table shown verbatim; never default, guess or narrow the scope.
4. A changed endpoint, source, model, ontology or description changes the plan ID and needs fresh approval; later commands reuse the journaled description.
5. Inventory accepts `.md`/`.txt` plus PDFs, Office files, HTML and images as original bytes. When any non-text file is present, add `--content-understanding-endpoint https://<name>.services.ai.azure.com` to `plan`; otherwise the plan blocks with `CONTENT_UNDERSTANDING_REQUIRED`. Say one plain line ("PDFs detected, will use Content Understanding"). The account must be in a Content Understanding region (not centralus), hold a deployment named like the chat deployment, and grant the Search identity Cognitive Services User.

New managed extraction plans bind requested page parallelism 64; never pass `--extraction-parallelism` unless the user asks for an override. Retain resolved `extraction_parallelism` through apply.

Search API `2026-11-01-preview` has no extraction output budget, and its Knowledge Source has no reasoning-effort setting; the runtime sets the generated extraction skill's `extraction.reasoningEffort` to `low`. Every graph build or attach sends its ontology as one inline JSON-LD string converted by the CLI (a deferred build sends none); never hand-write it. For Serverless, model extraction estimates exclude billable Compute Units, indexed storage, and Blob usage (ongoing cost is unknown, not zero).

Graph planning checks the chat model against the `modelName` values the `2026-11-01-preview` Search spec admits; other models are reported as not admitted by that Search API.

For canonical IDs, pass `--grounding-index <name>` before planning, give the producer `grounding.graph_name`, and re-plan once readiness passes; never copy a graph name from an ungrounded plan.

## Apply and publish

1. Show the card. After the user approves, run these in order directly in the main session shell (`initial_wait: 600` for `apply`), never inside a subagent. `<plan flags>` is everything between `plan` and `--json` above, unchanged (drop estimate-only `--chat-capacity`, `--trial-report`, `--upload-concurrency` from verify and publish):

   ```bash
   entity-graph-build apply <plan flags> --plan-id <plan-id> --confirm-writes --wait --json
   entity-graph-build verify <plan flags> --json
   entity-graph-build publish <plan flags> --json
   ```

2. `APPLY_INCOMPLETE` or an uncertain result is not success: run `progress`, then `reconcile`, then `verify`, each with `<plan flags> --json`. Never reapply around uncertainty. For local status read `run_id` from that journal; do not substitute the plan ID.
3. `publish` writes the descriptor under `~/.entity/descriptors` (or `$ENTITY_HOME`) and marks it current. Retain its returned descriptor path. `--keep-current` preserves the old current pointer.
4. Pass the serving descriptor as `--descriptor` on later plans so reader grants carry forward.

## Return

Verification compares the inline JSON-LD ontology by JSON value, so whitespace or
key-order differences in the service readback do not block. Any other difference does.

Report phase, exact plan ID, ontology mode, whether the result is offline planning or verified state, and one safe next action. After a verified publish, offer the [Graph Playground](../../graph-guide/references/install-and-checks.md#graph-playground) once.
