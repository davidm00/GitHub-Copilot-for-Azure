# Connect a knowledge base to an agent

## When to use

Connect one Prompt/Hosted Agent; conditionally create a missing agent.

## Do not use

Do not replace agents, attach multiple base tools, or handle base-free lifecycle.
Permission error is not absence; creation approval is separate.

## Inputs and discovery order

Resolve prompt, session, workspace, exact Azure readback, default, then one focused question.
Label sources; missing input blocks. Reads need no approval; silence approves nothing.

| Input | Why needed | Required? | Discovery order | Safe default | If missing or unanswered | Reconfirmation trigger |
|---|---|---|---|---|---|---|
| Base return/MCP endpoint | Grounding | Required | Session, exact proof | None | Block | Base/API/evidence change |
| Project ID/endpoint | Target | Required | Prompt, workspace, readback | None | Block | ID/tenant change |
| Agent name/inventory/type | Identity | Required | Prompt, readback | Never latest/type | Block ambiguity | Inventory/type |
| Definition/model/baseline; Hosted source/telemetry | Preservation | By branch | Exact readback | Preserve unrelated fields | Block | Protected state |
| Connection/tool; Hosted toolbox/environment | Binding | By branch | Full readback | One retrieve binding | Block conflict | Binding/endpoint |
| Principal/reader role | Retrieval | Before assignment | Readback | Exact Search scope | Block | Assignment |
| Grounding delta | Evidence | Required | Instructions | Base/citations/`I don't know` | Block loss | Delta |
| Acceptance/unrelated questions | Verification | Required | Baseline | None | Block | Questions |
| Persistence/cleanup owner | Ownership | Required | Prompt/session | None | Block | Owner |
| Provider/install or CLI choice | Missing agent | Conditional | Runtime, then choice | No automatic fallback | Block | Availability/choice |

## Decisions

Use [policy diagnostics](../references/search-substrate.md#azure-policy-diagnostics-after-creation-failure)
only after a creation failure implicates policy, never as a creation/delegation gate.

Read exact IDs/all scoped pages; inaccessible is not absent:

- **Prompt:** read all selected agent version pages, not Hosted resources.
  Normalize definition and same-label tools. Exact is zero-write;
  otherwise preserve all fields and add one `RemoteTool` with
  `ProjectManagedIdentity`.
- **Hosted:** compare project, deployment, source/config digest, environment, model,
  telemetry, ACR, connection, toolbox, identity, and tools. Exact is zero-write;
  unrelated or three-way conflict blocks. Read [Hosted connection](connect-hosted.md)
  before planning this branch's binding, access changes, or verification.

Only for a missing agent, load [missing-agent creation](create-missing-agent.md)
before questions/plans. Prefer `microsoft-foundry`: delegate approved
identity/configuration and known requirements. Otherwise offer installation
or Prompt CLI creation. Installation refusal is not creation approval.
Require a typed return with project, agent, version/deployment, model/status/identity
and definition/source/config/environment. Independently read back;
use fresh discovery and a new fingerprinted connection plan;
never carry creation approval. Incomplete returns block.

Discover Prompt schemas and read the KB through the exact preview API.
Model-free MCP requires `outputMode: extractiveData` and
`retrievalReasoningEffort: {kind: minimal}`, not unset GA defaults. Use the approved
[KB transition](../knowledge-bases/create.md#agent-compatible-minimal-transition).
Never change the KB implicitly or add a model as a workaround.
Only when authenticated Foundry MCP is unavailable or lacks a required operation,
load [typed Prompt SDK fallback](connect-prompt-sdk-fallback.md).
Denial/conflict blocks. Bind the surface; switching requires fresh review, never bypass.

## Proposed plan

List actions, before/after, API, identity/scope, network/data, cost, protected
digest, verification, cleanup owner, and retained resources.

## Confirmation

Present one immutable plan with `plan_fingerprint` and
`cleanup_approved: false`. Delegated creation is separate. A Hosted principal
known only after deploy requires a separate RBAC plan. Any known requirement or
protected-state readback change invalidates approval, except the bounded Prompt
connection warnings below; disclose these in the plan.

## Mutation

After confirmation, use the same deterministic identities; never retry another
name.

**Prompt:** Use the planned MCP or SDK surface; never invent operations.
Reconcile one `2025-10-01-preview`
`RemoteTool` connection with `ProjectManagedIdentity`, Search audience, and the
`2026-08-01-preview` KB MCP endpoint. Require the exact Search-service-scoped
`Search Index Data Reader` assignment. Preserve all fields; add at most one
same-label `MCPTool` with exact endpoint/connection,
`allowed_tools: ["knowledge_base_retrieve"]`, and `require_approval: "never"`.
Under the same agent name, require retrieval for every question, including
unrelated questions. Answer from retrieved evidence, not general knowledge;
unsupported answers are exactly `I don't know` without citations;
retrieval errors must remain errors. Approve exact appended instructions;
preserve previous instructions/versions. Duplicate labels block.

After exact identity/binding checks, `type` metadata differences and boolean
`isSharedToAll: true`-to-`false` restriction warn without rewriting. Missing/malformed
sharing, broader access, wrong target/auth/audience/category/required metadata
block. Apply the same rules to reuse; require actual agent tests below.

**Hosted:** Follow the selected [Hosted connection](connect-hosted.md) procedure.
Only approved missing resources, binding differences and required deployments
are writes; exact existing state skips them all. Never replace the agent or
rewrite source to attach its KB.

## Verification

Verify protected fields, a `knowledge_base_retrieve` call with original
citations, and unrelated `I don't know` without citations. Preserve behavior;
rerun with stable IDs and zero configuration writes. Account separately for
requested invocations, conversations/sessions and their usage. Record actual
tool execution and returned evidence separately from answer behavior; unavailable
payloads leave payload-level faithfulness unverified, not an inferred empty result.

## Failure and partial completion

Preserve first status/message/request ID. Denial, conflicts, incomplete
delegation, failed citations, unknown principal or drift blocks/partials.
Record writes, evidence, ownership, recovery and warnings; never widen state.

## Cleanup

Separate fingerprinted cleanup deletes only run-owned artifacts in reverse.
Prompt uses `helpers/prompt_cleanup.py` with exact digests. Hosted returns
`hosted-cleanup-unsupported`, zero writes, retaining all resources.
Unclear ownership blocks.

## Return contract

Return `completed`, `blocked`, or `partial` per shared schemas, with exact
resources/actions, invocation/readback evidence, ownership, first failure,
warnings and cleanup status.

## References

- [Shared audit schemas](../references/platform-contracts.md).
- [Interface versions](../references/platform-interfaces.md).

Authorities: failure/conflict/uncertainty only.

- [Connect Agents to Foundry IQ knowledge bases](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
