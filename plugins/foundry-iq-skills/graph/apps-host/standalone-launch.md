# Scope, environment and launch

Replace paths, published descriptors and the service origin with the approved
installation and data scope. Add only required feed/authentication environment
entries; do not copy the entire parent environment. The official stdio SDK adds
its documented small safe platform environment baseline, not arbitrary inherited
`PYTHONPATH`, Topic Graph defaults or provider secrets. Each domain's `env` is explicit.
The working directory defaults to the operator JSON's directory. An explicit
`cwd` must be an existing absolute directory outside the installed plugin,
including after resolving symbolic links. Keep config, caches and mutable state
outside the installed payload. Runtime bootstrap owns dependency verification
and environment selection; the Apps host does not duplicate that policy.
Topic Graph permits an optional explicit `tenant_id`; it does not permit query-key auth
or test-only `documents` in this production launcher. Existing authentication
must already be available; launch does not sign in or change any tenant.

```powershell
& 'C:\operator\node22\node.exe' `
  'C:\installed plugin\graph\apps-host\launch.mjs' `
  --config 'C:\operator\knowledge-apps.json'
```

The launcher resolves its parent plugin and these exact installed entries:

| Domain | Bootstrap domain | Apps entry and fixed flags |
|---|---|---|
| Ontology | `ontology` | `ontology-apps --state-dir <fixed>` |
| Entity Graph | `entity` | `entity-apps --descriptor <fixed>` |
| Topic Graph | `topicgraph` | `topicgraph-mcp --descriptor <fixed> --endpoint <fixed> --auth entra` |
| Grounding | `grounding` | `grounding-apps` with supplied `--index`, `--endpoint`, `--graph-name` |

Grounding accepts fixed `descriptor_path`, `index`, `endpoint` and `graph_name`
tool scope. Its descriptor path is not a startup flag; supplied index, endpoint
and graph name are also passed to the Apps entry. See the
[four-domain example](standalone-configuration.md) for descriptor/index requirements.

An ontology version is pinned in every advertised tool that accepts `version`;
the state directory itself is fixed on server startup. Browser arguments cannot
change paths, endpoints, credentials, process commands, environment or version.
The customer config cannot supply arbitrary executable/argument bindings.
On macOS/Linux use native absolute paths (for example `/usr/bin/python3`
and `/home/operator/...`), not the Windows example paths.
The same Node launcher and installed relative payload are used on all platforms.

## L1 topic diversity in Why Graph

The **Topic diversity** select at the end of the **Try:** row applies to the next comparison.
See [defaults, native setup prerequisites and request behavior](standalone-topic-diversity.md).

[Prerequisites and setup](standalone-setup.md) | [Launch](standalone-launch.md)
