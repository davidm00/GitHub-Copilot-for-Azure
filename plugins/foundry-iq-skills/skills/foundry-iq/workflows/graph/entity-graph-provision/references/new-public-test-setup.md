# New public-test setup

## Quick starts

- "Plan a new isolated public-test setup for Entity Graph."
- "Set up Entity Graph for a public corpus."

## Use this path

Use this path to create all resources in a new resource group from an empty subscription, in one approval. Only bounded public modes may apply.

New Search services default to Serverless. With `--public-data-entra`, Search defaults to East US 2 EUAP (`eastus2euap`), the only region serving the graph API (`2026-11-01-preview`) so far, and `plan` refuses others; storage and models use `--location` (default `westus3`). Check regional offerings and management API `2026-09-01-preview` read-only; no automatic Dedicated fallback. Serverless has no aliases or outbound private indexer networking. IP allowlists require an explicitly chosen compatible Dedicated SKU. Serverless usage cost is unknown, not zero; provisioning does not prove managed Blob graph extraction.

## Plan: run exactly

Confirm the tenant before sign-in. Fill placeholders with your own proposals, nothing else; never ask for names one by one:

- `<tenant>`, `<sub>`, `<user>`: `az account show --query "[tenantId,id,user.name]" -o tsv` (`<alias>` is `<user>` before `@`, lowercase letters/digits up to 12 chars). Never run `az account tenant list` or install extensions.
- `<short>`: `fiq` plus date and 2 random chars, such as `fiq1029k7`. `<rg>` is `<alias>-rg-<short>`. A group an earlier plan made can be reused: `plan` keeps what's there and lists only new changes.
- `<oid>`: `az ad signed-in-user show --query id -o tsv` (operator's four roles, minus any held directly, via a group or a parent scope (card: "Already held"; never re-add). Search system-assigned identity, the default, gets container-scoped Blob Data Reader on `<st>`, OpenAI User, and Blob/Table Data Contributor on `<cache>`. Add `--search-identity-name <alias>-<short>-uai` only if the user opts in to a user-assigned identity).
- `<srch> <st> <cache> <oai>`: `<alias>-<short>-srch`, `<alias><short>st`, `<alias><short>cache`, `<alias>-<short>-oai`; `<st>` and `<cache>` are 3–24 lowercase letters/digits (`StorageV2`). `--cache-same-as-source` instead of `--cache-storage-name <cache>` is explicit opt-in only and warns that Search receives write access on `<st>`.

Before `plan`, show one defaults view: tenant/sub, `<rg>`, resource names, Serverless Search in `eastus2euap`, storage and models in `westus3`, models `text-embedding-3-small`/`gpt-5.6-luna` (or "latest"), and Search identity: system-assigned (default) or, if the user opts in, a new user-assigned `<alias>-<short>-uai` (adds `--search-identity-name`). Ask once: use defaults (recommended) or override any? Never pick another region yourself.

Entra-authenticated public endpoints (`--public-data-entra`, no IP rules or private networking):

```bash
entity-graph-provision plan --tenant-id <tenant> --subscription-id <sub> --resource-group <rg> --create-resource-group --location westus3 --public-data-entra --search-name <srch> --storage-name <st> --cache-storage-name <cache> --openai-name <oai> --storage-container public-documents --operator-object-id <oid> --embedding-deployment embedding --chat-deployment chat
```

Synthetic public test (synthetic data only):

```bash
entity-graph-provision plan --subscription-id <sub> --resource-group <rg> --create-resource-group --location westus3 --public-test --public-test-mode entra_only --public-test-tenant-id <tenant> --public-test-expires-at <expiry> --synthetic-data-only --search-name <srch> --storage-name <st> --cache-storage-name <cache> --openai-name <oai> --storage-container public-documents --operator-object-id <oid> --embedding-deployment embedding --chat-deployment chat --json
```

Every flag shown is required except `--location` (default `westus3`). Models are checked against quota read-only. Do not add `--content-understanding-name`, `--network-*` or `--search-sku`, or mix public-test and public-data flags. Do not probe flags with trial runs; on an error, fix only the flag it names. User overrides or re-plans may change `--location` or names, or add `--search-location`, `--openai-location`, `--search-subscription-id` with `--search-resource-group` (Search apart from data), `--embedding-model`, `--chat-model`, `--embedding-capacity` or `--chat-capacity`.

`ip_allowlist` mode needs exact VPN egress hosts and deny-default firewalls. Neither mode enables trusted-service bypass.

## Apply

Every plan uses `arm-429-v1`: bounded retries of HTTP 429 only (listed in the card's
details), and **no automatic workflow replay or cleanup**.

1. If `plan` is blocked (`POLICY_DENIED`, `SEARCH_REGION_UNAVAILABLE`, `SEARCH_GRAPH_API_UNAVAILABLE`, `EXISTING_RESOURCE_CONFLICT`), nothing was created: follow its `next_step`, asking the user for another subscription or region. If the quota check reports a shortfall (`MODEL_QUOTA_SHORT`), do not show the card. Explain it and offer to re-plan within reported headroom (`--embedding-capacity`, `--chat-capacity`) or with another model or region (`--chat-model`, `--location`); show only the new card. Otherwise show the card; the plan already checked region, quota, roles and existing resources, so look nothing up. Don't recite the retry rules.
2. Ask one Approve/Stop question; never ask the user to type an ID, and re-show the card if the question is cancelled. Then run the plan's `apply_command` exactly, in this conversation with `initial_wait: 600`, and wait; never a subagent or background shell (it replays the saved `plan_file`; copy it, never retype flags). It checks quota and each subscription's needed Actions first, journals each step, and stops on the first failure. On `APPROVAL_REQUIRED`, read `differences`: changed flags are your execution error (rerun `apply_command`, no new approval); only changed held roles need a new plan and card.
3. Apply then runs a read-only connect. When it's `ready`, pass `--build-args <build_args_file>` to later steps. Otherwise wait a few minutes and run the connect command its next step prints (its arguments are kept in `.\.entity\connect-args.json`). After a failure, review the journal and re-plan; resume needs `plan-resume` approval.

Public-data recovery uses the same flags and the latest stopped `--run-id`, including an incomplete linked continuation. `plan-resume` binds the immutable root and full journal lineage hashes plus freshly validated owned resources, preserving the group and proposing only missing operations. Positive creation receipts remain valid even when a later guard failed; never recreate those resources. Refuse foreign, drifted, ambiguous or disconnected state and stale/competing lineage; an absent uncertain write needs a recorded HTTP429, not an unresolved timeout.

Validity uses stable approved identity, ownership, desired security, model/capacity and exact container/role invariants. Raw ARM snapshots and ETags remain audit evidence: provider-managed metadata evolution during approved child creation is allowed only while all validated invariants still match. ARM resource IDs compare case-insensitively, not arbitrary URLs or tags. After a new approval, `resume-apply --plan-id <new-id> --confirm-writes` rechecks quota, permissions and drift, records a distinct hash-linked journal, and stops without automatic workflow replay or cleanup. Request retries follow the source journal's bound policy. Positive acceptance receipts remain separate from subsequent polling failures; GET 404 after an accepted write is not noncreation proof or permission for another PUT. Every prior journal stays unchanged. Never rerun ordinary `apply`, rename resources or create missing pieces manually.

## Return

State what was planned or applied and the next action. Upload, build, and publish need separate approvals.
