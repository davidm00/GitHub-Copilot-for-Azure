# Decision guide

## Quick starts

- "Do I need a graph for vendor impact questions?"
- "What does the policy say about per diems?"

## Techniques

| Technique | Domain | What it gives you | Leaf skills |
|---|---|---|---|
| Knowledge graph | `entity-graph-skills` | Entities and relationships from documents; multi-hop answers with a path and a cited source per hop | [`entity-graph-provision`](../../entity-graph-provision/entity-graph-provision.md), [`entity-graph-build`](../../entity-graph-build/entity-graph-build.md), [`entity-graph-consume`](../../entity-graph-consume/entity-graph-consume.md) |
| GraphRAG | `topic-graph-skills` | A hierarchy of topics built from chunk vectors in a Search index, written to a separate `topicgraph-*` index. Preview | [`topic-graph-build`](../../topic-graph-build/topic-graph-build.md), [`topic-graph-consume`](../../topic-graph-consume/topic-graph-consume.md) |
| Candidate ontology | `ontology-skills` | An OWL ontology proposed from a Topic Graph build's topics and original source passages, refined, approved by you and exported as JSON-LD. Preview | [`ontology-build`](../../ontology-build/ontology-build.md), [`ontology-consume`](../../ontology-consume/ontology-consume.md) |
| Grounding index (optional) | `grounding-skills` | An index of known entities and edges (CSV, JSONL, Parquet or a bounded Wikidata seed) so a knowledge graph build resolves names to canonical IDs. Independent of Topic Graph | [`grounding-provision`](../../grounding-provision/grounding-provision.md), [`grounding-build`](../../grounding-build/grounding-build.md), [`grounding-consume`](../../grounding-consume/grounding-consume.md) |

## Which retrieval

- **Plain retrieval:** the answer sits in one or two passages. Prefer the `foundry-iq` skill in `foundry-iq-skills`. Entity Graph with ontology `none` is document retrieval only.
- **Knowledge graph:** no passage links vendor to customer, so vector search finds the vendor and stops. The graph walks vendor, project, customer and cites each hop.
- **GraphRAG:** themes across the corpus. It needs an index that already holds chunk vectors, no ontology, and never changes that index.

GraphRAG gives coverage and a knowledge graph gives precision; GraphRAG topics (GraphRAG calls these communities) also feed a candidate ontology.

## Ontology for Entity Graph

| Option | Pick it when |
|---|---|
| `deferred` (Recommended default at creation) | You have no ontology file yet: the Knowledge Source gets graph extraction with no ontology, so Search only chunks and embeds. Topic Graph topics and a generated OWL ontology serialized as JSON-LD (`.jsonld`) come from those chunks; the ontology is attached afterwards |
| `inline_jsonld` / `owl_file` (custom schema) | You bring your own OWL ontology serialized as JSON-LD (`.jsonld`), or `ontology-build` (`ontology-skills`) generated one from the Topic Graph build output. Attach it to the `deferred` build, or set it at creation when you already have it |
| `schema_org` (built-in fallback) | You want no custom ontology: attach the built-in business ontology (`Organization`, `Person`, `Product`, `Place`, `Event`) to the `deferred` build |
| `none` | Document retrieval only; no graph is built |

**Why not set an ontology at creation:** any ontology on the new Knowledge Source starts triple extraction right away. Create it with `--ontology deferred`, build topics and the ontology from the chunks, then attach with `entity-graph-build plan-attach-ontology`. Attaching reuses the cached chunks and embeddings, so only triple extraction runs. An attached ontology cannot be removed.

## Hand-offs between domains

The runtimes are independent; these are artifact hand-offs only:

1. Topic Graph reads any Search index with chunk vectors, including Entity Graph's.
2. `ontology-skills` (`ontology-build`) reads a Topic Graph build output folder locally, plus selected passages from the original source index. It does not need the Topic Graph to be published.
3. `ontology-build` exports an approved OWL ontology serialized as JSON-LD (`.jsonld`), which Entity Graph takes as `--ontology inline_jsonld --ontology-path <file.jsonld>` (or `--ontology owl_file --ontology-path <file.jsonld>`). Keep the same ontology flags through plan, apply, verify and publish.
4. `grounding-skills` (`grounding-build`) builds an index Entity Graph takes as `--grounding-index <name>`. Its `graph_name` must match the Entity Graph graph name and it needs label rows; `grounding-build` handles both.

Each domain owns its approvals. Nothing in Azure changes until you approve the exact change shown.

## Repeat and parallel runs

- Give each independent build its own state folder (`--state-dir`, or a separate grounding/Entity build journal). Re-planning in the same folder with changed inputs makes a new plan; it never reuses the old plan's results.
- Updates to one Entity Graph generation run one at a time. A second concurrent update is refused ("another update is running for generation X"), and staged content that changed under an update is marked `conflicted` instead of published.
- Each Topic Graph source (Search service and source index) and each ontology state folder keeps its own "current" record. Publishing one never changes another or makes its approval stale. With several, consumers ask for `--descriptor` (Topic Graph) or `--state-dir` (ontology) with `CURRENT_AMBIGUOUS`.
- Grounding keeps one descriptor per Search service and index; the same index name on two services needs `--endpoint`.
- Parallel builds on one machine are not a supported workflow; the runtimes refuse the unsafe overlaps rather than coordinate them.

## Presentation

Optional Apps (ontology, Entity Graph, Topic Graph and grounding) render in a compatible host.
The plugin includes a localhost MCP Apps host for their actual advertised documents. It displays
selected context, not an agent conversation. Neither replaces the ordinary CLI route.

## Wrong premises

Both consume skills check a question's premise. Both corrected the one wrong-premise question in the
chain run: one question on one corpus, not a guarantee.
