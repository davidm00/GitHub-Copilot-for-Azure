# Deferred ontology, then attach

This is the default graph path: the ontology is discovered from the corpus itself. Search chunks and embeds the documents once; attaching the ontology later
reuses that enrichment cache and only runs triple extraction.

1. Plan, apply, verify and publish as in [Plan and publish](plan-and-publish.md) with `--ontology deferred`. The Knowledge
   Source is created with graph extraction and the enrichment cache on, but no ontology. The
   published descriptor has a content index and no graph index or Knowledge Base yet. `verify`
   passes only after chunking and embedding finish for every document, or after the user
   accepts the documents that failed ([Failed documents](status-and-telemetry.md#failed-documents)).
2. Build topics from that descriptor's content index with `topic-graph-build`, then
   generate and export an ontology from that Topic Graph build output with `ontology-build`.
   A user who already has an OWL file can skip this step.
3. Plan the attach with the same flags as the deferred apply, changing only the ontology and
   adding the deferred descriptor:

   ```bash
   entity-graph-build plan-attach-ontology <plan flags with --ontology inline_jsonld --ontology-path <ontology.jsonld>> --descriptor <deferred-descriptor.json> [--trial-report <trial-report.json>] --json
   entity-graph-build attach-ontology <same flags, without --trial-report> --plan-id <attach-plan-id> --confirm-writes --json
   ```

   After a GO trial of this ontology, pass its saved `trial-report --json` output as `--trial-report` so the card shows the measured cost and time.
   `--ontology schema_org` also works when the user wants no custom ontology; `none` and `deferred` are refused.
   An attached ontology cannot be removed; offer a strict-subset trial of a custom ontology first
   ([Trial, update, retire](trial-update-retire.md)). Show the approval
   card and ask one Approve/Stop question.
4. Attach updates the existing Knowledge Source in place (ETag-guarded), waits for triple
   extraction, verifies the graph index, creates the planned KB (`<prefix>-kb-<generation>`
   for named runs, legacy `entity-kb-<generation>` otherwise) and rewrites the
   descriptor. Generation, Knowledge Source and index names do not change. While it waits it
   prints `Still extracting the graph: x/y documents (n min)` at least once a minute; for status
   questions see [Status while a step runs](status-and-telemetry.md#status-while-a-step-runs).
5. `ATTACH_WAITING`: a service rebuild is pending; rerun the same `attach-ontology` command.
   `ATTACH_STALE`: the Knowledge Source changed since planning; re-plan. Never edit the
   Knowledge Source by hand to get around either. `ATTACH_PARTIAL`: some documents failed
   extraction; offer investigate or accept ([Failed documents](status-and-telemetry.md#failed-documents)),
   pass `--descriptor <deferred-descriptor.json>` to `failures` and `accept-failures`, then rerun
   the same `attach-ontology` command.
6. Verify an attached build with `entity-graph-build verify <same flags> --descriptor <attached-descriptor.json> --json`.
   It already has its Knowledge Base, so skip the KB handoff. In-place `update` of an attached
   build is not supported yet; rebuild instead.
7. For requested topic Search/KB setup, return the final attached descriptor's
   KS/KB to the owning graph workflow for separately approved native topic
   activation with the same verified topic generation and state directory.
   Attach creates the KB, not native topic profiles. Report retrieval setup
   incomplete until activation and readback succeed; local publication alone
   enables browsing only.

## Enrichment cache and troubleshooting

- **Cache RBAC preflight:** Before creating a Knowledge Source, verify the Search system-assigned identity (`search.identity.principalId`) has both `Storage Blob Data Contributor` and `Storage Table Data Contributor` on the `StorageV2` enrichment-cache account (`doctor --cache-storage-resource-id <id> --search-resource-id <search-id>`). On `2026-11-01-preview`, `ingestionParameters.cache` omits `identity` (passing `cache.identity` triggers a server-side `DataIdentity` deserialization HTTP 400 on `/indexers/validate`), so `ResourceId=` cache access authenticates with the Search service's system-assigned managed identity with shared-key access disabled. If either role is missing, block and route to `entity-graph-provision connect`; otherwise the Knowledge Source PUT succeeds and the indexer fails later.
- **`enableReprocessing: true` required:** When `graphExtraction` is set on `2026-11-01-preview`, `ingestionParameters.cache.enableReprocessing` must be `true` (HTTP 400 otherwise). A Knowledge Source created without an enrichment cache requires a full rebuild to seed the cache.
- **`"type name"` error:** An unknown-property or `"type name"` error means a non-preview API version was called or the stamp does not serve `2026-11-01-preview`.
- **Large-corpus cache backlog & deletion sync:** Seeding writes chunks and embeddings to Blob (`ms-az-search-indexercache-<id>`) and Table (`MsAzSearchIndexerCache*<id>`) storage and can build a backlog across indexer windows on large corpora. The managed data source detects deleted blobs only when blob soft delete is on for the source account; otherwise a blob deleted outside `entity-graph-build update` keeps its chunks and triples (`update` removes its own deletions). `plan-retire` / `retire` cleans up the cache container and tables.
