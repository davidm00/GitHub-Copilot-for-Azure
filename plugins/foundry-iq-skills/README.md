# Foundry IQ Skills

Diagnose Foundry IQ and Azure AI Search access and ingestion issues, and configure Azure AI Search and Foundry IQ with source-aware security and verified API guidance. Build and query entity graphs, topic graphs and ontologies over your documents.

## Telemetry

The `track-telemetry` hook installs a pinned native `ghcfa-telem` release asset
when needed, verifies its platform-specific SHA-256 digest before extraction,
and caches the executable for reuse. To opt out of telemetry collection, set
`AZURE_MCP_COLLECT_TELEMETRY=false` in the environment of the process running
the agent.

## Skill

- [`foundry-iq`](skills/foundry-iq/SKILL.md): Azure AI Search and Foundry IQ guidance, diagnosis and configuration, plus entity graphs, topic graphs, graph-backed grounding and ontologies.

## What it helps with

- Diagnose Azure AI Search and Foundry IQ access, connectivity, ingestion and freshness failures
- Configure search, indexes, queries and knowledge sources using official Azure AI Search documentation and verified API versions
- Keep caller, search service identity and end-user authorization distinct for protected content
- Build and query entity knowledge graphs, topic graphs and graph-backed grounding passages over your documents
- Draft, version, validate and export ontologies
- Run a guided Foundry IQ graph demo

## Prerequisites

- [Git](https://git-scm.com/downloads), required to add the plugin marketplace
- [GitHub Copilot CLI](https://github.com/github/copilot-cli)
- Access to the Azure subscriptions and resources involved in your request
- An authenticated Azure identity with the permissions required for the requested read or change
- For graph features: [Node.js](https://nodejs.org/) and Python 3.12, 3.13 or 3.14 on the host. The graph runtime never installs Python; set `FOUNDRY_IQ_PYTHON` to an absolute interpreter path if none is found on `PATH`.

If you use Azure CLI for authentication, install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and sign in:

```bash
az login
```

## Installation

Run these commands in Copilot CLI:

```text
/plugin marketplace add microsoft/azure-skills
/plugin install foundry-iq-skills@azure-skills
```

To update the plugin:

```text
/plugin update foundry-iq-skills@azure-skills
```

## Example prompts

- "Why can't my search service read from this Blob container?"
- "My indexer stopped picking up new documents. What's wrong?"
- "Which API version should I use for a knowledge base request?"
- "Build an entity graph over these documents and find how these teams are connected."
- "Show me what Foundry IQ graph can do."

## Before changes are made

The skill asks for approval before billable, permission, network, production, destructive, credential or data-movement changes. The graph demo asks its questions once, then shows each approval before it changes Azure or spends money.

## Graph runtime and optional MCP Apps host

The `foundry-iq-graph` MCP server starts `node ${CLAUDE_PLUGIN_ROOT}/graph/runtime/launch-python.mjs`, which prepares an isolated, hash-locked Python runtime on first use. `graph/runtime/manifest.json` records wheel, source and dependency provenance. See [route checks](skills/foundry-iq/workflows/graph/graph-guide/references/install-and-checks.md) for details.

An optional localhost MCP Apps viewer ships in `graph/apps-host`; see its [README](graph/apps-host/README.md) for prerequisites.

## Learn more

- [Azure AI Search overview](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
- [Foundry IQ and agentic retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-overview)
- [Azure AI Search API and SDK versions](https://learn.microsoft.com/azure/search/search-api-versions)
- [Azure MCP Server tools for Azure AI Search](https://learn.microsoft.com/azure/developer/azure-mcp-server/tools/azure-ai-search)
- [Foundry IQ skill details](skills/foundry-iq/SKILL.md)
