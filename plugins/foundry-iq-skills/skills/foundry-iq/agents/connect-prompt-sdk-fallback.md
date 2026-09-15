# Existing Prompt Agent SDK fallback

Use this fallback only when authenticated Foundry MCP is unavailable or lacks a
required connection/version operation. Never bypass authorization denial or
conflicting state. Select it before planning; do not load it on a capable MCP path.
Require the parent's approved child fingerprint before ARM connection creation;
do not read policy unless a creation failure implicates it.
Unsupported required settings block, never disappear from the request. Read
`helpers/contracts.md` before constructing the plan. Verify the installed SDK
version and signed-in Azure CLI identity first. Only if dependencies are missing
or incompatible, obtain approval before installing:

```powershell
python -m pip install --pre "azure-ai-projects>=2.3.0,<3" "azure-identity>=1.25.0,<2"
```

Run `az login` only if unauthenticated; never silently change tenant or identity.
Both ARM and SDK execution use the signed-in Azure CLI context; the SDK and
shared cleanup loader use `AzureCliCredential`, not an environment/managed-identity
credential chain. Missing CLI authentication blocks noninteractively, never falls
back to another identity. Keep the selected CLI context unchanged during execution.
SDK failures retain safe provider code, HTTP status and server request ID
(`x-ms-request-id`, then `request-id`); unavailable status/ID stays null,
with a generic code when no safe provider code exists. Ambiguous outcomes keep
their workflow code and original failure status/ID.
Client request IDs are not server provenance; raw exception text is withheld.
After plan approval, invoke:

```text
python helpers/prompt_connect.py --input <approved-envelope.json>
```

The approved plan binds a project resource ID and endpoint that identify the
same account/project, existing agent name/version/model and protected-definition digest, absent or exact ARM
connection, Search knowledge-base MCP endpoint, exact
`allowed_tools: ["knowledge_base_retrieve"]`, `require_approval: "never"`,
verified `Search Index Data Reader` assignment ID/principal/scope, permission
forwarding mode, owner, and `cleanup_approved: false`.
Bind the exact appended evidence-only text in `grounding_instructions`;
old envelopes cannot authorize a grounding-text upgrade. Require retrieval
for every question, including unrelated questions, and never use general
knowledge to fill missing evidence. Distinguish tool errors from no support.

Exact `grounding_instructions` value (one line):

```text
For every user question, call knowledge_base_retrieve before answering, including questions that seem unrelated to the knowledge base. Answer only from evidence returned for that question and cite the original sources. Do not answer from general knowledge or assume an answer without retrieval. If the retrieved evidence does not support an answer, reply exactly: I don't know. Do not add citations to an unsupported answer. If retrieval fails, report the failure instead of treating it as no evidence or answering from general knowledge.
```

The helper is bounded to that existing version. It blocks model, type,
connection, duplicate same-label MCP tools, and same-label MCP tool drift;
preserves the serialized definition; reuses the sole existing exact desired
version or creates at most one ARM connection and one version under the same
agent name through `project.agents.create_version`; reads both back; and emits
compact JSON. Full-version comparison normalizes only the selected MCP tool's
list versus `tool_names` object encoding for `allowed_tools` (including
`read_only: null`); other fields remain strict. Equivalent versions must be
reused without calling `create_version`, not merely without new version IDs.
Apply the same normalization to ambiguous-create recovery and post-create
verification; preserve unknown fields and unrelated tools. Approval/ownership
digests bind the original readback, never its normalized copy.
Permission
forwarding is either not applicable or a named `search_auth_token` structured
input whose value exists only per request. Exit `2` means no-write blocked; exit
`3` means partial or ambiguous write and must not be reported as success.

The connection uses the Foundry project resource type
`Microsoft.CognitiveServices/accounts/projects/connections`, not the legacy
Machine Learning workspace type. Disclose the requested sharing flag
(`connection.is_shared_to_all`, default `true`) and the actual readback.
Server type metadata differences and a boolean `true`-to-`false` sharing
restriction warn rather than trigger a rewrite or duplicate connection.
Missing/malformed sharing evidence, broadened access, or identity, target,
auth, audience, category and required-metadata mismatches still block.
An explicit sharing `false` also rejects a nonempty `sharedUserList`.
Warnings survive later agent failures; readback reports actual sharing.
Apply this comparison consistently to creation, ambiguous-write recovery and
reuse; preserve the full agent-definition checks. A helper `completed` result
verifies configuration only: the parent's actual agent invocation, citations
and unsupported-question checks remain required.

Connection approval excludes cleanup. After separate approval, invoke:

```text
python helpers/prompt_cleanup.py --input <approved-cleanup-envelope.json>
```

The cleanup plan names only exact run-owned agent versions and connections,
binds each readback definition digest plus the connection ETag, deletes the
version before its connection, and verifies absence. It never deletes prior
versions, the project, model, knowledge base, or shared role assignments.
