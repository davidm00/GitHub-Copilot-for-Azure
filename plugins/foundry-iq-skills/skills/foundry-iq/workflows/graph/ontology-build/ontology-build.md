# Ontology build

First read [runtime setup](../graph-guide/references/install-and-checks.md#plugin-and-clis); use its `run <domain>` launcher.

Load one path only.

| Intent | Load |
|---|---|
| Set up, connect, inspect the topics, or plan and run a proposal | [Connect, plan, propose](references/connect-plan-propose.md) |
| Refine a draft, run one critique, or apply a critique | [Refine, critique, revise](references/refine-critique-revise.md) |
| Review, approve, import, export, or hand off the current ontology | [Review, approve, export](references/review-approve-export.md) |

## Shared rules

Run `ontology-build doctor --json` first. Add `--json` to every verb; read `next_step` and `error_code`, but if Azure checks skip or block, use [prerequisites](../graph-guide/references/install-and-checks.md#missing-prerequisites). Input: a Topic Graph build output folder (read locally), read-only access to its original source index, and an Azure OpenAI deployment. The Topic Graph does not need to be published.

Show each runtime `approval` card verbatim, then ask one Approve/Stop question; never ask the user to type an ID before `propose`, `refine`, `critique` or `approve`; never write or paraphrase your own approval text, never promise behavior the plan doesn't state, never create Azure/Search objects or role assignments outside the skill CLI (no raw `az`/REST workarounds), and stop and report the blocker when the CLI blocks. Take the model from `--build-args` or the user's explicit choice; never infer one. Pass the exact IDs from the command output. Never use `--force` on export unless asked. Never assign roles; show the printed command for an owner. Don't self-install tooling, read the runtime source or use Azure MCP tools. Entra only. Keep secrets, tenant details and passage text out of output.
