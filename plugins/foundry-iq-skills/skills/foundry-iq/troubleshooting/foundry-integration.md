# Foundry grounding: cross-system checks

Use the official [Foundry connection guide](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
for product setup and supported interfaces. These checks cover verification
across the existing agent, connection and Search runtime, not another setup recipe.
Follow the [API version policy](../references/api-version-policy.md) with the
original request version as input; do not silently change it.
Apply the [HTTP contract](../references/http-contract.md) and
[access safeguards](../references/safety-and-idempotency.md#access-and-credentials).

- Inspect the actual deployed agent version and tool trace. A working developer
  query does not prove that the agent's identity or execution network works.
- Distinguish KB MCP from classic binding; a successful connection write or direct
  Search query does not prove that the deployed agent used the intended tool.
- Require the actual tool call, a known fact and original-source citations.
  Missing calls, pending tool approval and service errors are incomplete.
- Apply approved corrections under [existing-agent safety](../references/safety-and-idempotency.md#existing-agent-changes);
  for native Search tools, use [classic binding](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/ai-search).
  Preserve settings and approval policy. Use [verification](../references/validation.md)
  for returned source evidence, not a second connection or replacement agent.
- Keep draft verification separate from production. Require actual-runtime
  verification and explicit cutover approval; report missing evidence as unverified.
