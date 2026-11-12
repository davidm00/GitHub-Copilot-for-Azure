# Foundry IQ Skills

Build grounded knowledge experiences with [Azure AI Search (Foundry IQ)](https://learn.microsoft.com/azure/search/agentic-retrieval-overview).

This plugin helps GitHub Copilot CLI use Azure AI Search and Foundry IQ, improve retrieval quality, and work with knowledge graphs, using your existing Azure resources when possible.

## Telemetry

The `track-telemetry` hook installs a pinned native `ghcfa-telem` release asset
when needed, verifies its platform-specific SHA-256 digest before extraction,
and caches the executable for reuse. To opt out of telemetry collection, set
`AZURE_MCP_COLLECT_TELEMETRY=false` in the environment of the process running
the agent.

## Skill

- **foundry-iq**: Azure AI Search and Foundry IQ guidance, retrieval-quality evaluation, and graph workflows.

## What it helps with

- Follow verified Azure AI Search and Foundry IQ API guidance
- Investigate Foundry grounding and connectivity failures
- Measure retrieval quality against a baseline and compare improvements
- Choose, provision, build, and consume entity graphs, topic graphs, ontologies, and grounding workflows
- Apply source-aware security and explicit approval before resource changes

The skill routes requests to curated workflows where available and otherwise uses official Azure AI Search documentation. It does not cover unrelated Azure products or continuous evaluation.

## Prerequisites

- [Git](https://git-scm.com/downloads), required to add the plugin marketplace
- [GitHub Copilot CLI](https://github.com/github/copilot-cli)
- [Python 3.12](https://www.python.org/downloads/), required for the bundled graph runtimes
- [Node.js](https://nodejs.org/), required for the graph MCP launcher
- Access to the Azure subscriptions and resources involved in your request
- An authenticated Azure identity with the permissions required for the requested read or change

If you use Azure CLI for authentication, install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and sign in:

```bash
az login
```

The graph runtime includes dependency locks for Windows x64, Linux x64/ARM64, and macOS Apple Silicon. Cold setup needs network access to the configured Python package source. Setup creates isolated environments outside the plugin; it does not download Python. The plugin registers Azure MCP and the entity graph MCP server, while the other graph adapters use explicitly scoped launches described in the skill.

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

- "Create a knowledge base from `./docs`."
- "Create a knowledge base from this Blob container."
- "Query this knowledge base with citations."
- "Connect this knowledge base to my existing agent."
- "Why is retrieval from this knowledge base failing?"

## Before changes are made

The skill starts with read-only checks and can reuse Azure resources you identify. It asks whether to use an existing service, find compatible services, or create a new one before performing broader discovery.

It asks for your approval before it:

- Creates an Azure AI Search (Foundry IQ) service, knowledge source, or knowledge base
- Connects a knowledge base to an agent
- Makes another planned change to Azure resources

Approval applies to the plan shown to you. If the plan changes, the skill asks again. Cleanup is handled as a separate planning workflow. The skill can also perform supported deletion of workflow-owned resources after separate approval.

## Learn more

- [Azure AI Search (Foundry IQ) overview](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
- [Foundry IQ and agentic retrieval](https://learn.microsoft.com/azure/search/agentic-retrieval-overview)
- [Azure AI Search (Foundry IQ) API and SDK versions](https://learn.microsoft.com/azure/search/search-api-versions)
- [Azure AI Search (Foundry IQ) REST API](https://learn.microsoft.com/en-us/rest/api/searchservice/?source=recommendations)
- [Azure MCP Server tools for Azure AI Search (Foundry IQ)](https://learn.microsoft.com/azure/developer/azure-mcp-server/tools/azure-ai-search)
- [Foundry IQ skill details](skills/foundry-iq/SKILL.md)
