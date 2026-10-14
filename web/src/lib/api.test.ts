import { ApiError, apiGet, apiPost } from './api';
import { mockBackend } from '../test-utils';

afterEach(() => vi.unstubAllGlobals());

/** The ApiError a call fails with. */
const failure = (p: Promise<unknown>): Promise<ApiError> =>
  p.then(() => { throw new Error('expected the call to fail'); }, (e: ApiError) => e);

describe('api', () => {
  it('returns the JSON body of a good answer', async () => {
    mockBackend({ 'health/': { body: { status: 'ok' } } });
    await expect(apiGet('health/')).resolves.toEqual({ status: 'ok' });
  });

  it("gives the backend's own error message for a refusal", async () => {
    mockBackend({ 'forecast/': { status: 400, body: { error: 'threshold must be between 0 and 1' } } });
    const err = await failure(apiPost('forecast/', { threshold: 2 }));
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(400);
    expect(err.message).toBe('threshold must be between 0 and 1');
  });

  it('says how to start the backend when it is not running', async () => {
    mockBackend({ 'health/': 'down' });
    const err = await failure(apiGet('health/'));
    expect(err.status).toBe(503);
    expect(err.message).toMatch(/Django backend not running/);
  });

  it('sends a JSON body with its content type', async () => {
    const calls = mockBackend({ 'forecast/': { body: {} } });
    await apiPost('forecast/', { antibiotic: 'ciprofloxacin' });
    expect(calls[0].init?.method).toBe('POST');
    expect(calls[0].init?.body).toBe('{"antibiotic":"ciprofloxacin"}');
    expect((calls[0].init?.headers as Record<string, string>)['Content-Type']).toBe('application/json');
  });

  it('reports a non-JSON answer with its status', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<html>oops</html>', { status: 500 })));
    const err = await failure(apiGet('models/'));
    expect(err.message).toMatch(/non-JSON response \(HTTP 500\): <html>oops/);
  });
});
