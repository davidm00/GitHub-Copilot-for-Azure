import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

it.each([
  ["rejects changed or escaping runtime assets before setup", "RuntimeAssetTests"],
  ["rejects stale runtime receipts and installed-package drift", "RuntimeInventoryTests"],
  ["plans and creates prompt-agent drafts without stale writes or replay", "PromptBindingTests"],
])("%s", (_description, testCase) => {
  const fixture = fileURLToPath(new URL("./entrypoint_regressions.py", import.meta.url));
  const output = execFileSync(process.env.PYTHON ?? "python", ["-B", fixture, testCase], {
    encoding: "utf8",
    timeout: 120_000,
    env: { ...process.env, PYTHONNOUSERSITE: "1", PYTHONDONTWRITEBYTECODE: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  expect(output).toContain("Entrypoint regressions passed");
});
