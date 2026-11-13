# Native Topic Graph runtime

Topic generation uses the separate, self-contained **topicGraphBuildTool**
binary (`topicgraph.exe` / `topicgraph`) published publicly on GitHub at
`Azure/foundry-iq-tool-releases`. Python wheels contain the importer, release
downloader and verified launcher, not a Python clustering fallback or a bundled
executable. Normal plugin setup never downloads or runs native code.

| Native RID | Release asset | Extraction | Executable |
|---|---|---|---|
| `win-x64`, `win-arm64` | `topicGraphBuildTool-<version>-win-<arch>.zip` | Safe `.zip` extraction | `topicgraph.exe` |
| `linux-x64`, `linux-arm64` | `topicGraphBuildTool-<version>-linux-<arch>.deb` | Rootless `.deb` read, no `dpkg` or root | `topicgraph` |

The native Topic Graph build isn't available on macOS; it fails with `NATIVE_PLATFORM_UNSUPPORTED`.

## Download, approval and verification

1. **Plan.** When no verified binary is cached or supplied, `topic-graph-build plan`
   (or `download-native`) looks up the release this plugin pins, checks that its asset URL and
   `sha256:` digest match the pin, and adds a download step to the approval card naming the
   repository, release tag, asset and digest. If no release can be resolved, `plan`
   stops before approval.
2. **Download.** `apply` (or `download-native --approve-download --plan-id <id>`)
   downloads the asset into the per-user cache, checks GitHub's `sha256:` digest before
   extraction, refuses path traversal, links and device entries, and writes
   `receipt.json` with the executable's SHA-256. A cached binary is reused while the
   pinned tag and digest still match its receipt. A newer TopicGraph release is not used
   until a plugin update moves the pin. If the published asset no longer matches the pin,
   download stops with `NATIVE_RELEASE_MISMATCH`; report it rather than retrying.
3. **Run.** Before every native call the launcher checks the executable bytes against
   `receipt.json`, or a `checksums.sha256` beside an operator-supplied binary. A binary
   with neither is refused (`NATIVE_BINARY_CHECKSUM_REQUIRED`). An unknown native output
   schema fails with `NATIVE_SCHEMA_VERSION_UNSUPPORTED`. Output of build tool 1.0.7 or
   earlier, or a community-form topic index, fails with `TOPIC_GRAPH_LEGACY_FORM`: rebuild
   with the pinned tool and publish to a new topic index; nothing is converted in place.

The cache is `%LOCALAPPDATA%\foundry-iq-skills\runtimes\topicgraph\native` on Windows
and `~/.cache/foundry-iq-skills/runtimes/topicgraph/native` elsewhere. Set
`TOPICGRAPH_NATIVE_CACHE` or `FOUNDRY_IQ_RUNTIME_CACHE` to an absolute path to move it.

The launcher uses the first binary it finds:

1. The absolute path passed with `--native-binary`.
2. The `TOPICGRAPH_BUILD_BINARY` environment variable, then `TOPICGRAPH_NATIVE_BINARY`.
3. The verified release in the per-user cache.
4. On Linux, the installed package at `/usr/bin/topicgraph`.
5. `topicgraph` (or `topicgraph.exe`) on `PATH`.

Verification applies whichever path is found. Do not bypass it, synthesize native
outputs, substitute another binary or infer execution acceptance from lock resolution.

The executable reads the original Search source index directly. Its own `preflight`
command decides whether that source is readable before a build starts.

Read-only import of retained native artifacts is not a new native run, full source
coverage, successful upload, publication, or model-call authorization.
