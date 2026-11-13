# Cut over a preserved existing Foundry prompt agent

Conditional on an explicit **production cutover** request after a classic-tool
or KB-MCP candidate passed identity, citations, quality and network checks.
This does not create an agent or change its retrieval architecture. A verified
draft alone is not deployed production.

## Discover and approve

Resolve agent API `v1` independently of Search/connection versions; verify
SDK 2.4+ draft/release and endpoint-selector support. Use the existing
authenticated `AIProjectClient` with the approved preview opt-in. GET agent details with
`project.agents.get(agent_name)` and original/candidate versions with
`get_version`. Retain full definition, instructions/model/tools/resources,
metadata, description/blueprint, endpoint protocols/auth/card and selector
privately; never log credentials. Re-read before each write: concurrent change
blocks cutover, not an unconditional overwrite. If supported conditional
updates or a verified serialized routing owner cannot prevent races, stop.

Require exact production-write authority and approval for routing, model costs,
baseline pinning, release creation, canary and rollback. Replay the original
stable app/agent request from its real principal/network as a baseline.
Missing baseline/version/owner or protected-user enforcement is a blocker.

## Pin, release and verify

The stable endpoint defaults to **latest**, so pin the approved existing
baseline **before** creating any non-draft release. PATCH only the selector:

```http
PATCH <project-endpoint>/agents/<agent-name>?api-version=v1
Content-Type: application/merge-patch+json

{"agent_endpoint":{"version_selector":{"version_selection_rules":[{"type":"FixedRatio","agent_version":"<baseline-version>","traffic_percentage":100}]}}}
```

Read back the selector and preserved protocols/auth/card, then replay the
original stable-runtime baseline. Only after that, copy the exact verified
candidate into an immutable release using the authenticated `AIProjectClient`:

```python
from copy import deepcopy

candidate = project.agents.get_version(agent_name, candidate_version)
release = project.agents.create_version(
    agent_name, definition=deepcopy(candidate.definition),
    metadata=deepcopy(candidate.metadata), description=candidate.description,
    blueprint_reference=deepcopy(candidate.blueprint_reference), draft=False,
)
```

GET the returned version; compare full definition and metadata/description/
blueprint with the approved candidate using [semantic readback](validation.md#semantic-readback),
not raw SDK/JSON equality; identity/security settings, unknown writable fields
and approval digests remain exact. An uncertain create requires listing/
reconciliation, never blind retries. Invoke this release with a version-pinned
`agent_reference` and verify known fact, original-document citations, no-answer
behavior and differently entitled denial where required.

Recheck routing concurrency, then use the same PATCH body replacing only
`agent_version` with the verified immutable release. Read back and replay the
**original stable app/agent request** through its actual principal/network.
Fact, citations, identity and endpoint selection must all pass; only then
report cutover. Never route production directly to an unverified draft/latest.

## Recover, clean up and return

On failure restore the exact approved previous selector and replay the original
runtime; PATCH success alone is not rollback verification. Leave unresolved
state explicit. Never change instructions, model, unrelated tools, auth/card or
network to conceal failure. Delete only owned, unused candidate/release versions
via `project.agents.delete_version(agent_name, agent_version)` after dependency
checks/approval; never delete the baseline or pre-existing agent.
Return original/candidate/release IDs, selector before/after, request IDs,
original-runtime evidence, costs, ownership, rollback and blockers under
[output](output-contract.md), with no secrets/private content.

Sources: [Agent endpoint selection](https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent),
[SDK 2.4 version contracts](https://github.com/Azure/azure-sdk-for-python/tree/azure-ai-projects_2.4.0/sdk/ai/azure-ai-projects).
