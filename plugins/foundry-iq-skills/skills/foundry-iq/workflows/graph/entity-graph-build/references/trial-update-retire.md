# Trial, update, retire

## Use this path

Use this path for three follow-ons: an OWL trial build, an in-place update of a published generation, or retirement of unbound generations.

## OWL trial

Offer a 50-document trial only when the `owl_file` corpus has more than 50
documents; the user may skip it. A trial must be a strict subset. For a
49-document corpus, 10 is valid and 50 is not. Retain any explicitly selected
valid smaller size; use that same `<n>` for plan, apply and report.

1. `entity-graph-build plan --sample <n>` with the same flags and the ontology to test (`--ontology inline_jsonld --ontology-path <ontology.jsonld>`, never `deferred`). It has its own plan ID and card. For `blob_prefix`, `--sample <n>` caps the indexer's `maxItems` on the live source prefix; no blobs are copied.
2. After exact approval, `entity-graph-build apply --sample <n> --plan-id <id> --confirm-writes`.
3. After synchronization, `entity-graph-build trial-report --sample <n>` (add `--tenant-id` and the user's chosen `--openai-resource-id`, never an inferred default, for a dollar estimate). Report the summary, zero-hit classes and predicates, and the go or no-go decision. The extrapolation is a range; rare classes can miss a small sample.
4. After a go, save `trial-report --sample <n> --json > trial-report.json`, then attach the same ontology to the published deferred build with `--trial-report trial-report.json` ([Deferred ontology](deferred-ontology.md)). Without a deferred build, plan the full build without `--sample`, with a new `--build-journal` and `--trial-report trial-report.json`. Reusing the trial journal blocks with `BUILD_JOURNAL_IN_USE`.
5. A trial is never publishable. Its resources stay until a separately approved retire plan.

A complete cost estimate requires observed chat and embedding token usage and
both applicable prices. Missing usage or pricing leaves total cost **unknown**,
while any known role subtotals remain visible. Measured, priced zero is distinct
from missing data. These extrapolations are estimates, not Azure billing.

## In-place update

Use only when documents changed and the ontology, models, extraction settings, and source location did not.

1. `entity-graph-build plan-update` with the published descriptor and the new source manifest.
2. After the user approves, run `entity-graph-build update --plan-id <id> --confirm-writes`. It uses no new index slots. Only one update per generation runs at a time; a concurrent one is refused, and if staged content changed underneath, the update stops as `conflicted` without publishing. Re-plan then.
3. If it stops or waits, follow its one `next_step`; rerunning the same plan ID resumes.
4. If the plan says "this needs a rebuild", return to a normal build plan.

## Retire generations

1. `entity-graph-build generations --descriptor <serving descriptor>` for every descriptor that must stay protected.
2. `entity-graph-build plan-retire` for unbound generations only. Add `--storage-endpoint` and `--storage-resource-id` to include staged blobs (`local_path`/`zip_archive` generations only; customer `blob_prefix` blobs are never deleted or modified by retire), and show the blob prefix and count. When the generation's indexer reports `cache.id`, `plan-retire` also lists the enrichment-cache container (`ms-az-search-indexercache-<id>`) and tables (`MsAzSearchIndexerCache*<id>`) for approved deletion because they outlive the Knowledge Source.
3. After the user approves, run `entity-graph-build retire --plan-id <id> --confirm-writes`. Each delete is conditional on the ETag reviewed in the plan.

## Return

Separate measured evidence from proposed cleanup. State what was reviewed, what was changed or deleted, and what still needs approval.
