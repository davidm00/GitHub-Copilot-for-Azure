# Connect existing resources

## Quick starts

- "Check whether my existing Search, Storage, and OpenAI resources are ready for Entity Graph."
- "Connect Entity Graph to the resources in resource group `<rg>`."

## Use this path

Use this path when the user already has a Search service, a Storage account, and an Azure OpenAI or Foundry account.

## Install

Follow [runtime setup](../../graph-guide/references/install-and-checks.md#plugin-and-clis):
explicit `setup entity`, then `run entity entity-graph-provision --help`. Retain the `run <domain>` launcher
on later commands; warm run never installs.

## Flow

1. Confirm the tenant and subscription (`az account show --query "{subscription:name, id:id, tenant:tenantId}" -o json`). Ask by name: "You're signed in to **<subscription>**. Use it for the models? (yes / pick another)". Choose models in two read-only tiers. Tier 1 runs only if the user wants another subscription: `entity-graph-provision discover --tenant-id <tenant>` lists every subscription you can see, with counts of model accounts, Foundry projects and accounts where you hold an OpenAI role. Ask for one by name; show its table only if the user asks. Tier 2: `discover --tenant-id <tenant> --subscription-id <sub>` (or the `--sub-row <S> --discovery-id <id>` command tier 1 prints). Its table lists that subscription's usable chat and embedding deployments by model and region, the ones you hold a role on first; `--all` adds every `OpenAI` and `AIServices` account, Foundry project and unusable deployment. Show its table verbatim and ask which model to use for embedding, chat/extraction and, if different, KB answers, by name; never refer to row numbers. Never pick or guess a subscription or row for the user. Add `--resource-group` only when the user asks to narrow.
2. For each chosen row run the tier-2 `Command:`, `entity-graph-provision discover --tenant-id <tenant> --subscription-id <sub> --row <N> --discovery-id <id> --role <embedding|chat|kb>`. For a role in another subscription, repeat tier 2 there. If it reports the inventory changed, show the new table and ask again. Use the `args.entity` flags it prints. To create a new deployment instead, run `discover --models-for <account-id> --role <role>`, show the region's models, versions, SKUs and quota (the recommended default floor is marked; newer or higher-tier models listed are fine too), and pass the user's choice as `--<role>-model`, `--<role>-model-version`, `--<role>-sku` and, for a non-TPM SKU, `--<role>-capacity`.
3. Run connect with names or exact IDs for Search and Storage, a dedicated `StorageV2` cache (`--cache-storage-name`/`--cache-storage-resource-id`; `--cache-same-as-source` is an opt-in that gives the Search identity write access to source data), plus the `args.entity` flags (`--embedding-openai-resource-id`, `--chat-openai-resource-id`, `--kb-openai-resource-id` and their deployments). Search uses its system-assigned identity by default (`--use-system-identity`); pass `--search-identity-resource-id <id>` only if the user opts in to a user-assigned identity. If the `search.identity` check lists `attached_user_assigned`, tell the user and offer that opt-in once. If Search is in another subscription or resource group, add `--search-subscription-id <search-sub>` and `--search-resource-group <search-rg>` (or pass its exact `--search-resource-id`); connect looks it up there and blocks (`search.subscription_tenant`) unless that subscription is readable in the same tenant. Add `--documents <n>` for a throttle estimate:

   ```bash
   entity-graph-provision connect --tenant-id <tenant> --subscription-id <sub> --resource-group <rg> --search-name <search> --storage-name <storage> --cache-storage-name <cache> --storage-container <container> <args.entity flags> --json
   ```
4. `incomplete` lists missing inputs. With no cache flag it lists `candidates.cache_storage` (`StorageV2` accounts other than the source; `matches_provisioned_cache_name` marks the one `apply` created): ask the user to choose and re-run with `--cache-storage-name`; never fall back to the source account. `blocked` lists failed checks (Free tier, key-only auth, public container); if Search has neither a user-assigned nor a system-assigned identity, `setup_plan` offers to enable `SystemAssigned` on Search.
5. Review `capacity` (SKU, TPM, quota headroom) and `roles`. OpenAI access is diagnosed from observed DataActions/NotDataActions per account, not role names. `permission_coverage` is not `effective_access`. Covered custom roles need no duplicate grant; absent/unknown coverage needs authorization diagnosis, not an assumed grant. Role checks count grants to the principal and to any group it's in (nested too); a group-held role is `assigned` with `via_group` and never re-granted. If group membership could not be read, say so; don't propose a grant yourself.
6. `needs_setup` returns one `setup_plan` for a missing Search system identity, container, deployment, or proposed roles. Present only the runtime `approval_card` verbatim (never write or paraphrase your own approval text or run raw `az`/REST workarounds); after the user approves (one Approve/Stop question; never ask them to type an ID), run `entity-graph-provision connect-apply` with the same flags plus `--plan-id <id> --confirm-writes`. It re-reads, refuses on drift, stops on first failure, and never retries.
7. `ready` returns `build_binding.build_args`: the exact `entity-graph-build` target flags (`--subscription-id` and `--resource-group` are Search's). Reuse the observed ARM OpenAI endpoint unchanged; never invent an alias. Connect saves them to the file it prints as `build_args_file`; later commands take `--build-args <file>`.
On Windows, Azure CLI batch launchers run through that installation's bundled
Python so `$filter=atScope()` reaches ARM unchanged. A missing bundled Python is
an actionable prerequisite failure, not permission to retry through `cmd.exe`.

`SecuredByPerimeter`, `Disabled` and unknown public-network states are not
unrestricted access. Even `Enabled` and a successful host probe do not prove
Search-to-Storage or Search-to-OpenAI access. Diagnose each leg separately:
operator-to-service, Search ingestion identity-to-Storage container, and that
identity-to-model deployment. Check network/perimeter policy and data-plane
authorization for the actual caller and scope. Connect reports service-to-service
access as unverified; inference and ingestion need their own observed results.
Any alternative account/container, reader grant or perimeter exception needs
separate explicit approval. Never automatically copy data or modify managed sources.

## Return

State the connect status, failed checks, and the one safe next action.
