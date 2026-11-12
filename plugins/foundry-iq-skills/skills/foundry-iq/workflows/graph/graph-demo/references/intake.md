# Intake

The only questionnaire. Ask it after Act 1 in one message with numbered questions and the defaults filled in, so "defaults are fine" is a complete answer.

1. **Tenant.** Name it before any sign-in.
2. **Subscription and a new resource group name.** Ask "You're signed in to **<subscription>**. Use it for the models? (yes / pick another)". For another, ask for its name, show its models and re-ask item 3. Search goes in East US 2 EUAP, the only region with the graph features so far; storage and new models default to West US 3. Generate the group name; a group this demo made earlier can be reused, and the plan keeps what's already there.
3. **Models.** Show the Act 1 model table as is: usable chat and embedding models by name and region, the user's own first. Ask for one embedding model and one chat model by name, or "create new ones for me" (the default when none are usable). The user always picks the chat model, even when there's only one.
4. **Data.** Sample earnings calls (default), or the path to a local folder ([my data](byo-data.md)).
5. **Ontology.** Generated from topics (default), the path to a `.jsonld` file ([my ontology](byo-ontology.md)), or standard.
6. **Ontology spend cap.** Default $1.
7. **Trial size N.** Default 5.
8. **Grounding.** Skip, Wikidata seed, or the path to an entity file ([grounding](grounding.md)). Default: Wikidata seed for the sample, skip for a folder. For an entity file, also ask for its licence.

## Validate before the first card

| Input | Must hold | If not |
|---|---|---|
| Subscription | Access confirmed | Re-ask item 2 |
| Folder | Exists and is not empty; the build's inventory reports what will be indexed and what will be skipped | Re-ask item 4 |
| `.jsonld` | `ontology-consume check` passes | Re-ask item 5 |
| Trial size | 1 ≤ N < M, where M is the number of documents; with fewer than two documents there is no trial | Re-ask item 7 |
| Entity file | Exists; CSV, JSONL or Parquet; has the columns the grounding build needs; has a licence; within the edge limit | Re-ask item 8 |

Re-ask only the item that is missing or invalid; keep every other answer.

## Then show the plan

List the acts with the run's numbered cards and one line on what each creates or spends ([cards by path](story.md#cards-by-path)). Give the exact card count. Name the longer steps (build, topics, attach) without times. Then start Act 2.
