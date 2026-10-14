// Serves the built site (dist/) for a deployment: every file as it is, and
// index.html for any other path, so /forecast and the other pages open from
// a link too. Plain Node, no packages.   node server.mjs   (PORT, default 4173)
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIST = fileURLToPath(new URL('./dist', import.meta.url));
const PORT = Number(process.env.PORT) || 4173;
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon',
  '.woff': 'font/woff', '.woff2': 'font/woff2', '.csv': 'text/csv; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
};

/** The file under dist/ for a URL path, or null if there is none (never a path outside dist/). */
async function fileFor(urlPath) {
  let path;
  try {
    path = normalize(join(DIST, decodeURIComponent(urlPath)));
  } catch {
    return null;   // a malformed %-escape
  }
  if (path !== DIST && !path.startsWith(DIST + sep)) return null;
  try {
    const s = await stat(path);
    if (s.isFile()) return path;
  } catch { /* not there */ }
  return null;
}

createServer(async (req, res) => {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { Allow: 'GET, HEAD' }).end();
    return;
  }
  const urlPath = new URL(req.url ?? '/', 'http://localhost').pathname;
  const found = await fileFor(urlPath);
  // a missing bundle is a 404, never the page (it would be cached as the script)
  if (!found && (urlPath.startsWith('/assets/') || extname(urlPath))) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-cache' }).end('Not found');
    return;
  }
  const file = found ?? join(DIST, 'index.html');
  const headers = {
    'Content-Type': TYPES[extname(file)] ?? 'application/octet-stream',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    // Vite names bundles by their content, so they can be kept; index.html is checked every time
    'Cache-Control': urlPath.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
  };
  res.writeHead(200, headers);
  if (req.method === 'HEAD') {
    res.end();
    return;
  }
  createReadStream(file).on('error', () => res.destroy()).pipe(res);
}).listen(PORT, '0.0.0.0', () => console.log(`web/dist on http://0.0.0.0:${PORT}`));
