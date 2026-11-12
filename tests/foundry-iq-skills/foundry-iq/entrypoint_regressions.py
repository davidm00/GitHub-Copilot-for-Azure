"""Offline behavioral checks of the current shipped runtime and prompt-binding CLI."""

import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


PLUGIN = Path(__file__).resolve().parents[3] / "plugins" / "foundry-iq-skills"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load shipped entry point: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OfflineTests(unittest.TestCase):
    def setUp(self):
        for owner, name in (
            (socket.socket, "connect"), (socket.socket, "connect_ex"),
            (subprocess, "Popen"), (os, "execve"),
        ):
            guard = patch.object(owner, name, side_effect=AssertionError("Live network/process forbidden"))
            guard.start()
            self.addCleanup(guard.stop)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.bootstrap = load_module("shipped_bootstrap", PLUGIN / "runtime" / "bootstrap.py")

    def runtime_spec(self):
        with patch.object(self.bootstrap, "cache_root", return_value=self.root / "cache"):
            return self.bootstrap.specification("entity")[0]


class RuntimeAssetTests(OfflineTests):
    def test_status_rejects_corruption_and_escape_before_setup(self):
        spec = self.runtime_spec()
        manifest = json.loads((PLUGIN / "runtime" / "manifest.json").read_text(encoding="utf-8"))
        runtime = self.root / "runtime"
        runtime.mkdir()
        records = [spec["wheel"], spec["lock"]]
        for record in records:
            target = runtime / record["file"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((PLUGIN / "runtime" / record["file"]).read_bytes())

        for damage in ("wheel", "lock", "parent-path", "absolute-path", "manifest-schema"):
            with self.subTest(damage=damage):
                document = copy.deepcopy(manifest)
                expected_error = "Missing or changed runtime asset"
                if damage in ("wheel", "lock"):
                    record = spec[damage]
                    target = runtime / record["file"]
                    original = target.read_bytes()
                    target.write_bytes(original + b"corrupt")
                elif damage in ("parent-path", "absolute-path"):
                    document["runtimes"]["entity"]["wheel"]["file"] = (
                        "../outside.whl" if damage == "parent-path" else str(self.root / "outside.whl")
                    )
                    expected_error = "Runtime asset must be inside"
                else:
                    document["schema_version"] = 2
                    expected_error = "Unsupported runtime"
                (runtime / "manifest.json").write_text(json.dumps(document), encoding="utf-8")
                output, errors = io.StringIO(), io.StringIO()
                with patch.object(self.bootstrap, "ROOT", runtime), \
                        patch.object(self.bootstrap, "cache_root", return_value=self.root / "cache"), \
                        patch.object(self.bootstrap, "select_python", return_value=Path(sys.executable).resolve()), \
                        patch.object(self.bootstrap, "setup", side_effect=AssertionError("Setup forbidden")) as setup, \
                        contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    code = self.bootstrap.main(["status", "entity"])
                self.assertEqual(code, 1)
                self.assertEqual(output.getvalue(), "")
                self.assertIn(expected_error, errors.getvalue())
                setup.assert_not_called()
                self.assertFalse((self.root / "cache").exists())
                if damage in ("wheel", "lock"):
                    target.write_bytes(original)


class RuntimeInventoryTests(OfflineTests):
    def test_verification_rejects_stale_receipt_and_package_drift(self):
        spec = self.runtime_spec()
        environment = self.root / "prepared"
        python = self.bootstrap.python_path(environment)
        python.parent.mkdir(parents=True)
        python.touch()
        packages = {self.bootstrap.normalized(item["name"]): item["version"]
                    for item in spec["dependencies"]}
        packages[self.bootstrap.normalized(spec["wheel"]["name"])] = spec["wheel"]["version"]
        installed = {"prefix": str(environment), "packages": packages}
        receipt = {"key": "reviewed-artifact", "packages": packages}
        ready = environment / "ready.json"
        ready.write_text(json.dumps(receipt), encoding="utf-8")
        with patch.object(self.bootstrap, "installed", return_value=installed), \
                patch.object(self.bootstrap, "verify_entrypoints") as entrypoints:
            self.bootstrap.verify(spec, "reviewed-artifact", environment)
            entrypoints.assert_called_once_with(spec, environment)

        for damage in ("stale-key", "pinned-version", "extra-package", "wrong-prefix"):
            with self.subTest(damage=damage):
                observed = copy.deepcopy(installed)
                record = copy.deepcopy(receipt)
                if damage == "stale-key":
                    record["key"] = "previous-artifact"
                    message = "ready marker does not match"
                elif damage == "pinned-version":
                    name = self.bootstrap.normalized(spec["wheel"]["name"])
                    observed["packages"][name] = "0.0.0"
                    message = "pinned wheel/dependencies"
                elif damage == "extra-package":
                    observed["packages"]["unexpected-package"] = "1.0"
                    message = "package inventory changed"
                else:
                    observed["prefix"] = str(self.root / "different-environment")
                    message = "pinned wheel/dependencies"
                ready.write_text(json.dumps(record), encoding="utf-8")
                before = ready.read_bytes()
                with patch.object(self.bootstrap, "installed", return_value=observed) as inventory, \
                        patch.object(self.bootstrap, "verify_entrypoints") as entrypoints:
                    with self.assertRaisesRegex(self.bootstrap.RuntimeErrorDetail, message):
                        self.bootstrap.verify(spec, "reviewed-artifact", environment)
                    entrypoints.assert_not_called()
                    if damage == "stale-key":
                        inventory.assert_not_called()
                self.assertEqual(ready.read_bytes(), before)


class Model(SimpleNamespace):
    def as_dict(self, **_kwargs):
        def encode(value):
            if isinstance(value, Model):
                return value.as_dict()
            if isinstance(value, list):
                return [encode(item) for item in value]
            if isinstance(value, dict):
                return {name: encode(item) for name, item in value.items()}
            return copy.deepcopy(value)
        return {name: encode(value) for name, value in vars(self).items()}


class MCPTool(Model):
    def __init__(self, **values):
        super().__init__(type="mcp", **values)


class PromptAgentDefinition(Model):
    def __init__(self, **values):
        super().__init__(tools=None, tool_choice=None, instructions=None, structured_inputs=None)
        vars(self).update(values)


class PromptBindingTests(OfflineTests):
    def setUp(self):
        super().setUp()
        modules = {name: ModuleType(name) for name in (
            "azure", "azure.ai", "azure.ai.projects", "azure.ai.projects.models",
            "azure.core", "azure.core.exceptions", "azure.identity",
        )}
        self.client = MagicMock()
        self.client_factory = MagicMock()
        self.client_factory.return_value.__enter__.return_value = self.client
        modules["azure.ai.projects"].AIProjectClient = self.client_factory
        models = modules["azure.ai.projects.models"]
        models.AgentVersionDetails = SimpleNamespace
        models.MCPTool = MCPTool
        models.PromptAgentDefinition = PromptAgentDefinition
        models.StructuredInputDefinition = Model
        for name in ("HttpResponseError", "ResourceNotFoundError", "ServiceRequestError", "ServiceResponseError"):
            setattr(modules["azure.core.exceptions"], name, type(name, (Exception,), {}))
        modules["azure.identity"].AzureCliCredential = MagicMock()
        with patch.dict(sys.modules, modules):
            self.binding = load_module(
                "shipped_prompt_binding",
                PLUGIN / "skills" / "foundry-iq" / "scripts" / "bind_prompt_agent.py",
            )
        self.base = SimpleNamespace(
            name="agent", version="1", draft=False, status="active",
            definition=PromptAgentDefinition(
                model="existing-model", instructions="Keep these owner instructions.",
                tools=[Model(type="function", name="existing-tool")],
                temperature=0.25, structured_inputs={"existing": {"schema": {"type": "string"}}},
            ),
            metadata={"owner": "keep"}, description="Keep description",
            blueprint_reference={"name": "keep-blueprint"},
        )
        self.client.agents.get_version.return_value = self.base
        self.client.agents.list_versions.return_value = [self.base]

    def invoke(self, *extra):
        output, errors = io.StringIO(), io.StringIO()
        argv = [
            "bind_prompt_agent.py", "--tenant-id", "00000000-0000-0000-0000-000000000001",
            "--project-endpoint", "https://example.services.ai.azure.com/api/projects/project",
            "--agent-name", "agent", "--base-version", "1",
            "--connection-name", "existing-connection",
            "--mcp-url", "https://example.search.windows.net/knowledgebases/documents/mcp?api-version=2026-08-01-preview",
            *extra,
        ]
        with patch.object(sys, "argv", argv), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = self.binding.main()
        return code, output.getvalue(), errors.getvalue()

    def test_plan_and_stale_approval_never_write_or_mutate_base(self):
        original = copy.deepcopy(self.base)
        code, output, errors = self.invoke()
        self.assertEqual((code, errors), (0, ""))
        plan = json.loads(output)
        self.assertEqual(plan["status"], "planned")
        self.assertFalse(plan["created"])
        self.assertFalse(plan["activated"])
        self.assertEqual(plan["latestReleasedVersion"], "1")
        self.assertEqual(plan["mcpTool"]["require_approval"], "always")
        self.client.agents.create_version.assert_not_called()
        self.client.agents.list_versions.assert_called_with("agent", order="desc", include_drafts=True)
        self.assertEqual([call[0] for call in self.client.agents.method_calls], [
            "get_version", "list_versions",
        ])
        self.assertEqual(self.base, original)
        self.client.reset_mock()
        code, output, errors = self.invoke("--apply", "--expected-latest-version", "0")
        self.assertEqual((code, output), (1, ""))
        self.assertEqual(json.loads(errors)["status"], "blocked")
        self.assertIn("Latest released state changed", json.loads(errors)["error"])
        self.client.agents.create_version.assert_not_called()
        self.assertEqual([call[0] for call in self.client.agents.method_calls], [
            "get_version", "list_versions",
        ])
        self.assertEqual(self.base, original)

    def test_apply_preserves_settings_and_never_replays_uncertain_readback(self):
        original = copy.deepcopy(self.base)
        original_definition = original.definition.as_dict()
        for readback in ("verified", "failed", "not-draft"):
            with self.subTest(readback=readback):
                self.client.reset_mock()
                self.client.agents.create_version.return_value = SimpleNamespace(version="2")

                def get_version(_name, version):
                    if version == "1":
                        return self.base
                    if readback == "failed":
                        raise self.binding.ServiceResponseError("Synthetic readback unavailable")
                    created = self.client.agents.create_version.call_args.kwargs
                    return SimpleNamespace(
                        version="2", draft=readback != "not-draft", status="active",
                        **{name: created[name] for name in (
                            "definition", "metadata", "description", "blueprint_reference",
                        )},
                    )

                self.client.agents.get_version.side_effect = get_version
                code, output, errors = self.invoke("--apply", "--expected-latest-version", "1")
                self.client.agents.create_version.assert_called_once()
                sent = self.client.agents.create_version.call_args.kwargs
                self.assertIs(sent["draft"], True)
                self.assertEqual(sent["metadata"], original.metadata)
                self.assertEqual(sent["description"], original.description)
                self.assertEqual(sent["blueprint_reference"], original.blueprint_reference)
                definition = sent["definition"].as_dict()
                for name in ("model", "temperature", "structured_inputs"):
                    self.assertEqual(definition[name], original_definition[name])
                self.assertEqual(definition["tools"][0], original_definition["tools"][0])
                self.assertEqual(len(definition["tools"]), 2)
                self.assertEqual(definition["tools"][1]["allowed_tools"], ["knowledge_base_retrieve"])
                self.assertEqual(definition["tools"][1]["require_approval"], "always")
                self.assertTrue(definition["instructions"].startswith(original_definition["instructions"]))
                self.assertEqual(self.base, original)
                self.assertEqual([call[0] for call in self.client.agents.method_calls], [
                    "get_version", "list_versions", "create_version", "get_version",
                ])
                self.assertEqual(self.client_factory.call_args.kwargs["retry_total"], 0)
                if readback == "verified":
                    self.assertEqual((code, errors), (0, ""))
                    result = json.loads(output)
                    self.assertEqual(result["status"], "created")
                    self.assertTrue(result["draft"])
                    self.assertFalse(result["activated"])
                else:
                    self.assertEqual((code, output), (1, ""))
                    self.assertEqual(json.loads(errors)["status"], "blocked")
                    self.assertIn(
                        "readback failed" if readback == "failed" else "draft/readback validation failed",
                        json.loads(errors)["error"],
                    )


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False).result
    if result.wasSuccessful():
        print("Entrypoint regressions passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
