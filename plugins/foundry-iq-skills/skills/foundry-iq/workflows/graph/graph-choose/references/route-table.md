# Route table

## Quick starts

- "I have contract documents and need to know which vendors an outage affects."
- "I have earnings call transcripts and want to discover topic clusters and an ontology."

## Pick one row

| You have | You want | Route | Ontology |
|---|---|---|---|
| Documents | One passage, with citations | `foundry-iq` skill in `foundry-iq-skills` | none |
| Documents | Facts from single passages through Entity Graph | [`entity-graph-provision`](../../entity-graph-provision/entity-graph-provision.md) then [`entity-graph-build`](../../entity-graph-build/entity-graph-build.md) then [`entity-graph-consume`](../../entity-graph-consume/entity-graph-consume.md) | `none` |
| Documents, no OWL ontology file | Multi-hop answers across people, organizations, projects, products | [`entity-graph-provision`](../../entity-graph-provision/entity-graph-provision.md), [`entity-graph-build`](../../entity-graph-build/entity-graph-build.md) without an ontology, [`topic-graph-build`](../../topic-graph-build/topic-graph-build.md), [`ontology-build`](../../ontology-build/ontology-build.md), attach it with `entity-graph-build`, then [`entity-graph-consume`](../../entity-graph-consume/entity-graph-consume.md) | `deferred` at creation; attach the generated `.jsonld` (or built-in `schema_org`) |
| Documents and an OWL ontology file (`.jsonld`) | Multi-hop answers in your domain | same Entity Graph route | `inline_jsonld --ontology-path <file.jsonld>` (or `owl_file --ontology-path <file.jsonld>`) |
| A Search index with chunk vectors | Themes; what the corpus covers | [`topic-graph-build`](../../topic-graph-build/topic-graph-build.md) then [`topic-graph-consume`](../../topic-graph-consume/topic-graph-consume.md) | none needed |
| A Topic Graph build output folder | Generate a custom domain ontology | [`ontology-build`](../../ontology-build/ontology-build.md) then [`ontology-consume`](../../ontology-consume/ontology-consume.md) | produces OWL in JSON-LD (`.jsonld`) |
| An existing ontology file | Re-review it, or extend it against a public corpus | [`ontology-build`](../../ontology-build/ontology-build.md): offline import/review; extension needs a Topic Graph build output folder and a priced proposal | n/a |
| An approved `.jsonld` OWL ontology | Multi-hop answers with it | [`entity-graph-build`](../../entity-graph-build/entity-graph-build.md): optional strict-subset trial (`--sample <N>`, go/no-go), then attach it to the build created without an ontology; see [`graph-demo`](../../graph-demo/graph-demo.md) | `inline_jsonld` / `owl_file` with explicit exported `.jsonld` path |
| Documents, and you want the whole chain | Guided demo: one intake, then chunks, topics, ontology, trial, attach, questions | [`graph-demo`](../../graph-demo/graph-demo.md) | `deferred`, then attach `inline_jsonld` / `owl_file` (or `schema_org`) |
| Only an Azure subscription | A new workflow | Pick the outcome first; use its owning provision skill, not Entity Graph by default | route-specific |
| Known entities with canonical IDs, and a knowledge graph build | One ID per entity in answers | [`grounding-provision`](../../grounding-provision/grounding-provision.md), [`grounding-build`](../../grounding-build/grounding-build.md), [`grounding-consume`](../../grounding-consume/grounding-consume.md), then Entity Graph's grounding-index input | any except `none` |

A knowledge graph always needs an ontology: bring an OWL ontology serialized as JSON-LD (`.jsonld`), generate one with `ontology-build` (`ontology-skills`), or use the built-in `schema_org`. Without an ontology file, create the Knowledge Source with none (`deferred`) and attach it once generated. GraphRAG needs none.

Reuse ready deployments: published Entity Graph -> `entity-graph-consume`, published Topic Graph -> `topic-graph-consume`; an ontology to inspect -> `ontology-consume`. Do not route a read back through provisioning. Every Entity Graph build extracts the graph; multi-hop answers need a published build whose ontology has edge types (a deferred build has none until its ontology is attached).

## Rules of thumb

- Two hops and no single document states the link: knowledge graph (`entity-graph-build plan`).
- **Without an ontology file, create the Knowledge Source with no ontology (`--ontology deferred`).** Search then only chunks and embeds; setting an ontology at creation starts triple extraction at once. Build Topic Graph topics from those chunks, generate the OWL ontology serialized as JSON-LD (`.jsonld`) with `ontology-build` from that build output, then attach it. Attach built-in `schema_org` instead if the user wants no custom ontology.
- A question that starts from a wrong fact: `entity-graph-consume` and `topic-graph-consume` check the premise first.
- An attached ontology cannot be removed: offer a strict-subset trial (`--sample <N>`) of a custom `.jsonld` ontology first to review populated classes, relationships, time, and cost.
- Topic Graph and `ontology-skills` are previews. Ontology needs a Topic Graph build output folder; publishing is not required.
- Grounding is optional and independent of Topic Graph. Name the index before Entity Graph planning; pass `--grounding-index <name>` and hand `grounding.graph_name`, endpoint and index to its producer. After `ready`, re-plan Entity Graph and approve that exact plan. Never reuse an ungrounded name.

## Handoff

1. Run only the read-only checks in [Install and checks](install-and-checks.md) for the chosen route.
2. Show the install lines from that file only if missing; wait for the user.
3. Hand off in plain language to the first owning skill.
