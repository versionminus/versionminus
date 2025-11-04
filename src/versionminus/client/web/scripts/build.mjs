import { execSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

function runningInDocker() {
  try {
    if (process.env.DOCKER === '1') return true;
    if (existsSync('/.dockerenv')) return true;
    const cg = readFileSync('/proc/1/cgroup', 'utf8');
    return /docker|containerd/i.test(cg);
  } catch {
    return false;
  }
}

const hasLocalSdk = existsSync(path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..', 'sdk/ts/src/index.ts'));
const forceDocker = process.env.VM_BUILD_TARGET === 'docker';
const inDocker = forceDocker || runningInDocker();
// Prefer local source when available, unless explicitly building for Docker
const tsconfig = (!forceDocker && hasLocalSdk) ? 'tsconfig.build.dev.json' : 'tsconfig.build.json';

console.log(`[build] hasLocalSdk=${hasLocalSdk} forceDocker=${forceDocker} inDocker=${inDocker} using ${tsconfig}`);

try {
  execSync(`npx tsc -b ${tsconfig}`, { stdio: 'inherit' });
  execSync('npx vite build', { stdio: 'inherit' });
} catch (err) {
  process.exit(typeof err.status === 'number' ? err.status : 1);
}
