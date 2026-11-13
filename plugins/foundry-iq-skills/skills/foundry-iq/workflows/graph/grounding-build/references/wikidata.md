# Wikidata

## Quick starts

- "Bootstrap a grounding index from Wikidata for the seed `Q95`."
- "Plan a depth-2 Wikidata grounding index for `Microsoft`, capped at 20,000 edges."
- "Is Wikidata data OK to load into a grounding index?"

## Steps

1. Plan. Fill placeholders, nothing else; repeat `--seed` per seed, and `--depth` is 1 or 2:

   ```bash
   grounding-build plan --tenant <tenant> --endpoint https://<service>.search.windows.net --wikidata --seed <QID or title> --depth 1 --edge-cap 50000 --with-labels --graph-name <build graph name>
   ```

2. Show the plan card; wait for approval; then `grounding-build apply --tenant <tenant> --plan-id <plan-id>`.
3. Run `grounding-consume ready --index <name> --graph-name <graph name>`.

## Bounds

Seed-bounded only: at least one seed is required and full dumps are refused. Depth 1 reads the seed's statements; depth 2 also the entities they link to. The edge cap maximum is 50,000. If it would be exceeded the plan refuses rather than truncating; narrow the seeds or depth.

## What is loaded

The public Wikidata Action API is used with a descriptive User-Agent, a low request rate, `maxlag`, and retry on 429/503. Kept statement types: item, string, quantity (`object_double`), time (`object_datetime`, day precision or finer), English monolingual text. Deprecated and no-value statements are skipped. Subject and object are English labels, QIDs go in `subject_id`/`object_id`, predicates are property IDs such as `P31`. Every edge has confidence 0.9, origin label `wikidata:CC0`, and graph name `wikidata-<seed ids>` unless `--graph-name` replaces it.

## Licensing

Wikidata structured data is CC0 1.0: no attribution or ShareAlike obligation. The plan and descriptor record `wikidata:CC0`. Generic Wikidata edges add noise for private or niche corpora; prefer this mode for demos and public-domain topics.
