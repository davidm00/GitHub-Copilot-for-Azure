# Hand-offs

Exact commands between acts. Keep CLI flags, digests and journal paths in tool calls; the user sees plain updates ([story](story.md)). Each leaf skill of the `foundry-iq-skills` plugin owns its approval cards.

## 1. Resources

`entity-graph-provision apply` runs `connect`; when it's `ready` it saves `build_binding.build_args` (endpoints, ARM IDs, identity, deployments, models) to the file it prints as `build_args_file`. Pass `--build-args <file>` to every later command (Entity Graph, grounding, Topic Graph, ontology); never retype or synthesize a flag. If it isn't ready yet, wait a few minutes and run the connect command its next step prints.

Later acts reuse the run's chat and embedding deployments from that file; never ask about models again. Only if one is gone, run `entity-graph-provision discover --resource-group <the run's data group>` and recommend the run's own deployments first. Ontology also needs per-1M input/output prices.

## 2. Documents

Sample (never ask for a URL), fetched at Act 2, not during readiness, into the user's working directory:

```text
python -I "<package-root>\runtime\bootstrap.py" run entity entity-graph-build fetch-sample --output "<cwd>\earnings-corpus" --json
```

Use its `output` folder as `--source-reference` for `entity-graph-build inventory` and `plan`; keep `questions_file` for Act 7. A user's folder goes through the same `inventory` ([my data](byo-data.md)).

Build with no ontology: `entity-graph-build plan --build-args <file> --ontology deferred` with the source manifest, an absolute journal and `--source-description` drafted from a few documents. Search only chunks and embeds. After the user approves: apply, verify (waits for every document), publish. Keep the published descriptor, the plan flags and the journal unchanged; the trial and attach reuse them.

## Grounding

Only when chosen ([grounding](grounding.md)), before the build card:

1. `entity-graph-build plan ... --ontology deferred --grounding-index grounding-<name> --json` with the build inputs above. Read `grounding.index` and `grounding.graph_name`; the plan is blocked until the index exists, so show no card.
2. `grounding-provision doctor --build-args <file>`.
3. Wikidata: `grounding-build plan --build-args <file> --wikidata --seed Q2283 --depth 1 --index <grounding.index> --graph-name <graph name>`. Entity file: `grounding-build plan --build-args <file> --file <edges> --index <grounding.index> --graph-name <graph name> --license "<licence>"`. No preview: plan shows the card. Show it and ask one Approve/Stop question; then `grounding-build apply --build-args <file> --plan-id <plan-id>` with the plan ID from its output.
4. `grounding-consume ready --build-args <file> --index <grounding.index> --graph-name <graph name>` must pass; on failure follow its `next_step`.
5. Re-run the step 1 plan unchanged; its card is the build card.

The attach reuses the build flags, so it keeps `--grounding-index`; leave it out of the trial, which is a separate build with its own graph name. After the attach, report `grounding_coverage`.

## 3. Topics

Topic Graph reads the published content index in place; no copy is made. Put `--build-args <file>`, these global flags and an absolute `--state-dir` before every verb:

| Topic Graph flag | Value |
|---|---|
| `--source-index` | descriptor's content index |
| `--key-field` | `uid` |
| `--text-field` | `snippet` |
| `--vector-field` | `snippet_vector` |
| `--source-field` | `blob_url` |

`topic-graph-build inspect --json` must pass before planning; failed or unknown inspection blocks. Inspect, plan, apply, verify, then publish behind its own card. After approval run the plan's `apply_command` exactly; it names the right `--state-dir`. After publish, run its `browse.command` exactly to show the topics. Keep `generation_id`, the publish result's `browse.env.TOPICGRAPH_DESCRIPTOR` for browsing and the Sitemap, and the `topicgraph_output.directory` that `verify` reports.

## 4. Ontology

Generated: `ontology-build connect --build-args <file> --topic-graph-output <dir> --accept-current-source` with one absolute `--state-dir` on every command; then inspect, plan, propose (the spend card), review, approve (its card, one Approve/Stop question; run the approve command review printed), export to `<path>.jsonld`. Go straight from propose to review: no refine, critique or question check in the demo, and never write a questions file. Refine is an offer in the recap. `ontology-consume check` must pass; keep the `ontology-consume current --json` path, SHA-256 and source generation matching that export. Entity Graph needs object-property domain and range and rejects remote imports. A user's file: [my ontology](byo-ontology.md). Standard: `--ontology schema_org` at the attach.

## 5. Trial

For M documents in the complete manifest, use the intake's N with `1 <= N < M`; never pad the corpus or change the manifest. `entity-graph-build plan` with the binding, source, `--source-description`, `--source-manifest <manifest.json> --sample <N> --json`, the ontology (`--ontology inline_jsonld --ontology-path <path>.jsonld`) and a new journal. Apply with the exact plan ID, then `trial-report` with the same inputs. A trial cannot be published; no-go goes back to Act 4 with the zero-hit classes, where a priced refine is an offer the user can take. Trial resources stay until a separately approved retirement.

## 6. Attach

Same complete manifest and journal as the build, changing only the ontology, plus the published deferred descriptor; no `--sample`. An attached ontology cannot be removed.

```text
entity-graph-build plan-attach-ontology <build flags, --ontology inline_jsonld --ontology-path <path>.jsonld> --descriptor <deferred-descriptor.json> --json
entity-graph-build attach-ontology <same flags> --plan-id <attach-plan-id> --confirm-writes --json
```

Only extraction runs; it verifies the graph index, creates `entity-kb-<generation>` and rewrites the descriptor. `ATTACH_WAITING`: rerun the same command. `ATTACH_STALE`: re-plan. `ATTACH_PARTIAL`: the partial-ingestion stop. Status uses `run_id` read from the durable journal.

## 7. Questions

`entity-graph-consume query --graph --descriptor <descriptor> --query "<question>" --json` (`--query-mode nl2gql` or `kb` for Knowledge Base retrieval). Plain-search baseline: the same command without `--graph`; it answers from the top passages and names their sources. Use a question about named facts (people, products, figures). Historical scores are not a packaged runnable benchmark.

## Cleanup commands

Print, never run: `az group delete --name <resource group> --subscription <subscription>` for each group this run created (two when Search was placed apart). List the local folders it made (sample corpus, state directories) for the user to remove. Nothing else.
