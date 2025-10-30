/* eslint-disable @typescript-eslint/no-explicit-any */
// Fallback is used when runtime cannot access the filesystem (e.g. in browsers). Keep in sync with VERSION file.
const FALLBACK_VERSION = '1.0.0';
const VERSION_RELATIVE_PATH = '../../VERSION';

let cachedVersion: string | undefined;

declare const __dirname: string | undefined;

function tryGetDynamicRequire(): ((id: string) => any) | undefined {
  try {
    // Use Function constructor to avoid static analysis by bundlers.
    // eslint-disable-next-line no-new-func
    const maybeRequire = Function('return typeof require === "function" ? require : null;')();
    return typeof maybeRequire === 'function' ? (maybeRequire as (id: string) => any) : undefined;
  } catch {
    return undefined;
  }
}

function getImportMetaUrl(): string | undefined {
  try {
    // eslint-disable-next-line no-new-func
    return Function('try { return import.meta && import.meta.url ? import.meta.url : undefined; } catch { return undefined; }')();
  } catch {
    return undefined;
  }
}

function resolveVersionPath(path: any): string | undefined {
  const metaUrl = getImportMetaUrl();
  if (metaUrl) {
    try {
      const url = new URL(VERSION_RELATIVE_PATH, metaUrl);
      let resolved = path.normalize(url.pathname);
      if (/^\/[A-Za-z]:/.test(resolved)) {
        resolved = resolved.slice(1);
      }
      return resolved;
    } catch {
      /* no-op */
    }
  }

  try {
    if (typeof __dirname !== 'undefined') {
      return path.normalize(path.resolve(__dirname, VERSION_RELATIVE_PATH));
    }
  } catch {
    /* no-op */
  }

  return undefined;
}

function readVersionFromFile(): string | undefined {
  const dynamicRequire = tryGetDynamicRequire();
  if (!dynamicRequire) return undefined;

  try {
    const fs = dynamicRequire('fs') as any;
    const path = dynamicRequire('path') as any;

    const target = resolveVersionPath(path);
    if (!target) return undefined;

    const contents = fs.readFileSync(target, 'utf8');
    return contents.trim();
  } catch {
    return undefined;
  }
}

export function getVersion(): string {
  if (cachedVersion !== undefined) return cachedVersion;
  const fromFile = readVersionFromFile();
  cachedVersion = fromFile || FALLBACK_VERSION;
  return cachedVersion;
}
