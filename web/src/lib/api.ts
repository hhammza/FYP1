/* Calls to the Django API (backend/api/urls.py).

   Locally the Vite server passes /api through to port 8000; a deployed build
   sets VITE_API_URL to the backend's address (and the backend lists this
   site in CORS_ALLOWED_ORIGINS). Every failure comes back as an ApiError
   with a message fit to show on the page, as the Flask frontend gave. */

export const API_URL: string = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

/* /predict waits longer than other pages: a gene model runs AMRFinderPlus on
   the upload, 10-45 s per genome, on top of reading the genome. Kept below the
   backend's gunicorn --timeout (backend/Dockerfile). */
export const PREDICT_TIMEOUT_S = 120;
export const DEFAULT_TIMEOUT_S = 30;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const NOT_RUNNING = 'Django backend not running. Start it with: python manage.py runserver';

export interface RequestOptions {
  timeoutS?: number;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

async function request<T>(method: string, path: string, body: BodyInit | undefined,
                          opts: RequestOptions, json: boolean): Promise<T> {
  const timeoutS = opts.timeoutS ?? DEFAULT_TIMEOUT_S;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort('timeout'), timeoutS * 1000);
  opts.signal?.addEventListener('abort', () => ctrl.abort(opts.signal?.reason));
  const headers: Record<string, string> = { ...(opts.headers || {}) };
  if (json) headers['Content-Type'] = 'application/json';
  let r: Response;
  try {
    r = await fetch(apiUrl(path), { method, body, headers, signal: ctrl.signal });
  } catch (e) {
    if (ctrl.signal.aborted && ctrl.signal.reason === 'timeout') {
      throw new ApiError(`The backend did not answer within ${timeoutS} seconds. Try again; `
                         + 'if it keeps happening, the server is overloaded.', 504);
    }
    if (opts.signal?.aborted) throw e;
    throw new ApiError(NOT_RUNNING, 503);
  } finally {
    clearTimeout(timer);
  }
  const text = await r.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    // The Vite proxy answers with an empty or HTML body when Django is down
    if (r.status === 502 || r.status === 503 || r.status === 504 || r.status === 500 && !text) {
      throw new ApiError(NOT_RUNNING, 503);
    }
    throw new ApiError(`Backend returned non-JSON response (HTTP ${r.status}): ${text.slice(0, 200) || '(empty)'}`,
                       r.status);
  }
  if (!r.ok) {
    const err = (data as { error?: unknown }).error;
    throw new ApiError(typeof err === 'string' ? err : `Backend returned HTTP ${r.status}`, r.status);
  }
  return data as T;
}

export function apiGet<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  return request<T>('GET', path, undefined, opts, false);
}

export function apiPost<T>(path: string, payload: unknown, opts: RequestOptions = {}): Promise<T> {
  return request<T>('POST', path, JSON.stringify(payload ?? {}), opts, true);
}

/** A multipart upload (a FASTA or a CSV); the browser sets the boundary. */
export function apiUpload<T>(path: string, form: FormData, opts: RequestOptions = {}): Promise<T> {
  return request<T>('POST', path, form, opts, false);
}

/** The full URL of a backend path, also for a plain <a href> download (gene CSVs). */
export function apiUrl(path: string): string {
  return `${API_URL}/${path.replace(/^\//, '')}`;
}

export const errorText = (e: unknown): string => (e instanceof Error ? e.message : String(e));
