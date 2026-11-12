# Story

The demo makes one argument: search finds passages; a knowledge graph understands what's in them. Each act is one step in it. Say the user-facing lines below in plain words; keep commands, flags, digests and journal paths in tool calls.

## Voice

- Name things: the subscription, model, region and resource group. Never point at a row number or an ID.
- Ask one short question with a default, such as "Use it? (yes / pick another)".
- Costs come only from the cards and plan output ("about $X"); never look prices up. An unknown cost is "unknown".
- No jargon ("model discovery", "Azure CLI subscription") and no disclaimers ("this does not authorize changes or spending"). The cards cover approval.
- Ask about models, not regions; the region is only a column. Before the resources card, say in one line what it makes, such as "I'll create **gpt-5.6-luna** for chat and **text-embedding-3-small** for embeddings, with Search in East US 2 EUAP, where the graph features are. OK?"

## Opening

After the starter prompt, print this pitch word for word before running anything, then Act 1:

> Foundry IQ turns a folder of documents into something an agent can reason over.
>
> I'll take **49 Microsoft earnings calls (2014–2026)** and build three things on Azure AI Search: **topics** that show what the calls are about, an **ontology** that names the things in them, and a **knowledge graph** that connects who said what about which product. Then we'll ask questions that plain search can't answer well.
>
> I'll do the work. You approve anything that changes Azure or costs money. There will be up to **8 approvals**. I'll give you the exact count after your answers, and tell you before each one.
>
> Want to use your own documents or your own ontology instead? Tell me in your answer below.
>
> First, I'll check your machine and your Azure sign-in.

## Acts

1. **Readiness**: preflight, the sign-in check and the models in the signed-in subscription ([commands](install-and-checks.md#act-1-commands)). Preflight may prepare the plugin's runtimes; nothing touches Azure. "Your machine is ready. You're signed in to **<subscription>**, and here are the models you can use." Then the [intake](intake.md).
2. **Your documents become searchable.** Resources, then the sample or the user's folder, then the build with no ontology: chunks and embeddings only. "This is what search alone sees: passages and vectors. It can find text that looks like your question. It doesn't yet know that Satya Nadella is a person or that Azure is a product." With grounding, set it up here, before the build card ([grounding](grounding.md)). Show the document count and the plain-search answer, with its source, to one sample question about named facts (people, products, figures): the baseline for Act 7.
3. **Discover what the documents are about.** Topics read the chunk index in place with the run's chat model (no new model question), then publish, then the Sitemap from the one browse command publish prints. "Before we decide what things to extract, let's see what the corpus is about. Topics group passages by meaning, with no schema needed." Show the outline, broadest topics first with each share, and open one topic with a sample passage.
4. **Name the things that matter.** Generated: "The topics told us what the calls talk about. Now I'll turn that into an ontology: the types of things and how they relate. You review it before anything uses it." Go straight from the proposal to its review and approval, and say what it has in the card's words ("23 types of things, 40 links between them"). Approving it is a review, not an Azure write. Improving it with a reviewer model is offered at the end, not done here. Mine: see [my ontology](byo-ontology.md). Standard: "We'll use the standard business schema: organizations, people, products, places and events."
5. **Try before you commit.** "An ontology can't be removed once it's attached, so we test it on a few documents first and look at what it actually extracts." Show classes and relationships with hits and those with none. No-go returns to Act 4.
6. **Build the graph.** "Same documents, same index. Now Search extracts entities and relationships using your ontology. Because we chunked once, this step is only extraction." With grounding: "…and resolves each name against your grounding index." Warn that the ontology can't be removed.
7. **Ask questions search can't answer well**, then 8. **See it**: [finish](finish.md).

## Cards by path

Number a run's cards 1..N in this order, skipping those not chosen; that N is the exact count. Grounding is always before the build and never after attach.

- Generated ontology: resources · grounding (if chosen) · build · topics · publish · ontology spend · trial (recommended) · attach
- My ontology: resources · grounding (if chosen) · build · topics · publish · trial · attach
- Standard ontology: resources · grounding (if chosen) · build · topics · publish · attach

Data (sample or my folder) doesn't change the cards. Card purposes: resources creates the Azure resources; grounding creates the grounding index; build chunks and embeds; topics builds topics (model calls, compute billed separately); publish makes them browsable; ontology spend proposes the ontology (in dollars, capped); trial builds N documents with the ontology; attach adds the ontology and creates the graph and Knowledge Base.

Before each card, one plain line of what it does: "Card 4 of 7: this names about 40 topics in your index with gpt-5.4-mini." No caveats, other acts' budgets or IDs. After each act: **Done** (one line), **Why it matters** (one line), **Next** (the next act or card).

## Stops and recovery

| Stop | One next action |
|---|---|
| Card | Ask one Approve/Stop question; if it's cancelled, show the card again |
| Intake | Re-ask only the missing or invalid item |
| A command fails | One plain line to the user, never the raw error; run the command its next step names |
| Partial ingestion | Offer: investigate the failed documents, or continue without them |
| Policy block | Ask for another subscription for storage and models, then re-plan |
| Quota shortfall | Explain it and offer a re-plan |
| Search region without the graph features | Re-plan with Search in East US 2 EUAP; the models stay where they are |
| Resource group this demo didn't make | Re-plan with a new group name, such as the old name plus "-2" |
| Role not yet propagated | Show the role card, then re-check |

Resume with "Continue my Foundry IQ demo": find the run from the workspace's journals and descriptors and pick up at the last finished act.
