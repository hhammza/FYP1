import { readFileSync } from 'node:fs';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

/** The amrpredict package's version, for /library: read from its pyproject.toml,
    so the page cannot fall out of step with the package. */
function libVersion(): string {
  try {
    const toml = readFileSync(new URL('../amrpredict-lib/pyproject.toml', import.meta.url), 'utf-8');
    return toml.match(/^version\s*=\s*"([^"]+)"/m)?.[1] ?? 'unknown';
  } catch {
    return process.env.LIB_VERSION || 'unknown';
  }
}

// In development the Django API runs on port 8000; /api is passed through to
// it, so the browser sees one origin and no CORS setup is needed locally.
// A deployed build calls VITE_API_URL instead (see src/lib/api.ts).
export default defineConfig({
  plugins: [react()],
  define: {
    __LIB_VERSION__: JSON.stringify(libVersion()),
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
    // the sample responses (/predict/sample, /timeline/sample) are read from
    // progress/formats/ on a development run; a build leaves them out
    fs: { allow: ['.', '../progress/formats'] },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
    css: false,
  },
});
