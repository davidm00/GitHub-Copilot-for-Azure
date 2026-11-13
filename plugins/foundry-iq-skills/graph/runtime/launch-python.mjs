// Starts bootstrap.py with the first working local Python, so MCP hosts need only
// `node` on PATH. Bootstrap then selects the bound or discovered supported Python.
import { spawn, spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const bootstrap = join(root, 'bootstrap.py');
const versions = JSON.parse(readFileSync(join(root, 'manifest.json'), 'utf8')).python_versions;
const windows = process.platform === 'win32';
const override = process.env.FOUNDRY_IQ_PYTHON;
const candidates = [
  override && [override],
  ...[...versions].reverse().flatMap(version => [[`python${version}`], windows && ['py', `-${version}`]]),
  ['python3'],
  ['python'],
  windows && ['py', '-3'],
].filter(Boolean);

// Bootstrap itself needs Python 3.9+; the probe also skips app-store stubs that only print a hint.
function usable([command, ...prefix]) {
  const probe = spawnSync(command, [...prefix, '-I', '-c', 'import sys; print(sys.version_info >= (3, 9))'], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000, windowsHide: true,
  });
  return probe.status === 0 && probe.stdout.trim() === 'True';
}

const python = candidates.find(usable);
if (!python) {
  const tried = candidates.map(candidate => candidate.join(' ')).join(', ');
  process.stderr.write(`foundry-iq: no usable Python found (tried ${tried}). `
    + `Install Python ${versions.slice(0, -1).join(', ')} or ${versions.at(-1)}, `
    + 'or set FOUNDRY_IQ_PYTHON to its absolute path in this server\'s environment.\n');
  process.exit(1);
}

const [command, ...prefix] = python;
// stdio is inherited unchanged: MCP stdout must carry only protocol messages.
// On Windows, bootstrap exits when this PID dies, even with a Python trampoline in between.
const env = windows ? { ...process.env, FOUNDRY_IQ_LAUNCHER_PID: String(process.pid) } : process.env;
const child = spawn(command, [...prefix, '-I', bootstrap, ...process.argv.slice(2)], {
  stdio: 'inherit', windowsHide: true, env,
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
child.on('error', error => {
  process.stderr.write(`foundry-iq: could not start ${python.join(' ')}: ${error.message}\n`);
  process.exit(1);
});
child.on('exit', (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
