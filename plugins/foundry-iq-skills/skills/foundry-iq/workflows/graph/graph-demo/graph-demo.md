# Graph demo

Starter prompt: "Show me what Foundry IQ graph can do." The demo drives itself: one intake reply, then only approval cards. "Continue my Foundry IQ demo" resumes at the last finished act; there is no demo state file.

**Run it yourself.** Run each documented command in this conversation, say what it does first and wait for it to finish, Azure writes too. No subagents or background shells, no reading or importing runtime source, no scripts of your own, no Azure MCP tools, doc pages, help text or hand-made `az rest`. Never set `*_HOME` variables. Run any next command the output gives exactly. If a command fails, tell the user in one plain line, never the raw error, and follow its next step; run doctor only for sign-in problems.

| Need | Load |
|---|---|
| Opening, acts, cards, stops | [Story](references/story.md) |
| Intake and validation | [Intake](references/intake.md) |
| User's own folder | [My data](references/byo-data.md) |
| User's own `.jsonld` | [My ontology](references/byo-ontology.md) |
| Grounding | [Grounding](references/grounding.md) |
| Questions, recap, cleanup | [Finish](references/finish.md) |
| Exact commands | [Hand-offs](references/handoffs.md) |
| Act 1 commands, preflight | [Checks](references/install-and-checks.md) |

## Acts

1 Readiness, then intake. 2 Searchable documents: resources, grounding (if chosen), chunk-and-embed build. 3 Topics and publish, on every path. 4 Ontology. 5 Trial. 6 Attach. 7 Questions. 8 See it.

## Rules

- Ask every intake question in one message; validate before the first card.
- Before each card, say one plain line ("Card 4 of 7: this names about 40 topics in your index with gpt-5.4-mini."), show it verbatim, then ask one Approve/Stop question; never ask the user to type an ID. If the question is cancelled, show the card again. Never combine or auto-approve cards.
- Speak plainly (Voice in Story); no CLI flags, digests, journal paths or caveats.
