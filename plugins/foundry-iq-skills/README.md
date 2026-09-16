# Foundry IQ skills

Create a Foundry IQ knowledge base from local files, Azure Blob Storage, or an
ADLS Gen2 directory; retrieve answers with original-source citations; and connect
an existing Prompt or Hosted Agent to a knowledge base.

The `foundry-iq` skill guides resource intake, supported creation and reuse,
retrieval verification, read-only diagnosis, and ownership-aware cleanup.
It asks for approval before applying mutation plans. Supported source creation
is limited to File and Blob-family sources; other connectors, multi-source
creation or reconfiguration, classic Search index/query applications, and
production hardening are outside this contribution.

## Local build and use

From the repository root, run `npm run build`, then load the built plugin:

```bash
copilot --plugin-dir ./output/foundry-iq-skills
```

```powershell
copilot --plugin-dir .\output\foundry-iq-skills
```

For example: "Make my local contracts searchable in a knowledge base with
citations. Show me the costs before creating anything."

The plugin declares Azure MCP and uses the repository's shared, client-specific
hooks. Node.js and an authenticated Azure context are needed for applicable
operations; individual procedures explain Python helper and service prerequisites.
No live Azure operation is performed by building the plugin.

## Review status

This is a review draft, not a release-ready package. Plugin and skill version
bases remain `1.0`; the intended `0.1` release base is unresolved. Source metadata
uses `0.0.0-placeholder`, with real versions stamped only into build output.
Human content/metadata approval and two authoring-team code owners are pending.

The accompanying native eval suite grades skill invocation only, not successful
Azure task completion. Candidate-matched model, client, and Azure validation
must not be inferred from historical routing results.