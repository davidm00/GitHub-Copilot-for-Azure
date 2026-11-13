# Run naming

Use one saved naming context for the demo or a standalone workflow. Ask for a
short label, such as `travel`, `finance` or `mydocs`; propose a corpus-derived
default if none was given. Do not put personal information or document text in
resource names.

## Start, join and resume

Use the packaged launcher from [runtime setup](install-and-checks.md#plugin-and-clis).
This offline command starts a fresh run and writes only local naming metadata:

```text
python -I "<package-root>\graph\runtime\bootstrap.py" run entity entity-graph-provision name --run-name travel --output-root "<cwd>\.foundry-iq" --json
```

Keep its `run_naming.prefix`, `resource_names`, `run_directory`, `state_root`
and `provision_state_dir`. The prefix is `fiq-<label>-<8 lowercase hex>`;
labels normalize to lowercase ASCII letters, digits and single dashes, with
1-24 characters after normalization. Two new runs with the same label get
different prefixes. Never invent the random suffix or regenerate it mid-run.

Pass `--run-prefix <resolved-prefix>` and the returned `--state-dir
<provision_state_dir>` to provisioning or connect. For creation, missing
resource names default from the prefix; explicit names and existing resources
are retained. Connect saves versioned `run_naming` metadata and the exact
prefix in `build-args.json`. Pass that binding to subsequent stages rather
than reconstructing deployment or naming flags.

Standalone entry points can start with `--run-name <label>` or join with
`--run-prefix <resolved-prefix>`:

| Entry point | Where the naming context is saved |
|---|---|
| `entity-graph-provision plan` or `connect` | Parent of `--state-dir` (the provisioning journal folder); default `.entity` |
| `entity-graph-build plan` | Parent of `--build-journal`; default `.entity` |
| `topic-graph-build ... plan` | `--state-dir`; put naming/global flags **before** the verb |
| `ontology-build connect` | `--state-dir` |
| `grounding-provision create` or `grounding-build plan` | `--run-state-dir`; default `.grounding` |

Reuse that state directory and binding when resuming. `run-naming.json` freezes
the resolved context; conflicting labels or prefixes are rejected. A new run
needs a new state directory. Without naming flags or saved named context,
legacy workflows keep their existing names and generation identities.
Grounding preview does not save a context; its proposed random prefix is
provisional until plan.

## Artifact roles

For prefix `fiq-travel-12345678`:

| Artifact | Name |
|---|---|
| Resource group, Search, OpenAI, identity | `<prefix>-rg`, `-search`, `-openai`, `-identity` |
| Entity Knowledge Source | `<prefix>-entity-<generation>` |
| Entity content and graph indexes | Knowledge Source name plus `-index` and `-graph-index` |
| Knowledge Base | `<prefix>-kb-<generation>` |
| Topic index | `<prefix>-topics-<native-content-id>` |
| New topic retrieval profile | `<prefix>-retrieval-<vector-hash>` |
| Grounding index | `<prefix>-grounding` |
| Staged Entity files | `<container>/<Knowledge Source name>/...`; trials add `trial/` |

Storage and cache accounts require compact lowercase alphanumeric names of
at most 24 characters. Use the returned hashed suggestions (`st` and `ca`
suffixes), not a manually stripped prefix. Existing retrieval profiles are
reused, not renamed. Native content/generation IDs, operational `run_id`,
product schema identifiers and approval IDs keep their original meanings.

## Local layout and safety

For the demo, keep corpus, exports and separate `entity`, `topics`, `ontology`
and `grounding` state folders beneath the returned `run_directory`. Use
`entity\build-journal.json` for the full build and a separate trial journal;
keep the full build's journal for attach. Use `topics` and `ontology` as the
respective `--state-dir`, and `grounding` as `--run-state-dir`.

Ontology retains its versioned filenames beneath its selected state folder.
Grounding's `--run-state-dir` stores naming metadata only: saved plans and
descriptors still use its managed global storage. Never relocate them or set
`GROUNDING_HOME`; retain `saved_to` and the authoritative plan ID.
Entity's published descriptors also retain their managed
`~/.entity/descriptors` location; keep the returned descriptor path.

Naming does not rename existing resources, establish ownership, grant access
or approve writes. Keep exact-generation checks, descriptor protection,
source journals and all existing approval and retirement gates.
