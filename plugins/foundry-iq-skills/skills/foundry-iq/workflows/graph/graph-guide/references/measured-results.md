# Measured results

Reference outcomes from end-to-end walkthrough runs on the built-in **Microsoft Earnings Calls** dataset (`microsoft-earnings-calls`). Each reflects one corpus and ontology configuration rather than a universal guarantee across arbitrary datasets.

## Built-in `schema_org` vs. generated custom ontology (49 transcripts)

These runs set the ontology when the Knowledge Source was created. The current default creates it with no ontology and attaches one later; no measured run of that flow is published yet, so do not quote these numbers as its results.

- **Corpus:** 49 quarterly Microsoft earnings-call transcripts (`FY14Q4.txt`–`FY26Q4.txt`, `CDLA-Permissive-2.0`), materialized via `entity-graph-build fetch-sample`.
- **Built-in `schema_org` knowledge graph:** Extracted `1,545` indexed chunks and `4,945` graph edges (`72` `schema_org` ontology rows) in a single build, supporting multi-hop entity traversal, GQL queries, and cited Q&A with zero custom schema authoring.
- **Topic hierarchy (`topic-graph-build`):** Discovered `35` hierarchical topics (`2` levels, `2,286` memberships) from the content index's chunk embeddings.
- **Generated custom ontology (`ontology-build` + `entity-graph-build plan-attach-ontology --ontology inline_jsonld`):** `ontology-build` proposed `28` domain classes and `35` properties (`0` ontology profile violations) from the Topic Graph topics, gated by a 3-document strict-subset trial (`status: "go"`, `330` edges) before extracting `6,279` domain-tailored edges (`30.8%` grounded to canonical IDs via `grounding-build`).
- **Multi-hop Q&A (`entity-graph-consume` & `Why Graph`):** Both `schema_org` and custom ontology graphs support cited multi-hop traversal and premise checking; the opt-in custom ontology adds specialized domain predicates (such as mapping all 8 analysts in `FY24 Q4` to the executives who answered them).

## Summary of capabilities

| Capability | What is demonstrated |
|---|---|
| **Built-in `schema_org` knowledge graph** | Multi-hop entity and relationship extraction (`4,945` edges across 49 transcripts) with no custom OWL required (`entity-graph-skills`) |
| **Zero-schema topic discovery (GraphRAG)** | Hierarchical topics and representative passages built directly from chunk vectors (`topic-graph-skills`) |
| **Custom ontology generation** | Candidate `.jsonld` OWL schema proposed from topics (`28` classes, `35` properties) and gated by a strict-subset Entity Graph trial (`ontology-skills`) |
| **Premise verification** | Detects and corrects false premises in user questions using cited transcript evidence |
