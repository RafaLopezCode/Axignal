import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import http from 'node:http';
import { once } from 'node:events';
import { setTimeout as pause } from 'node:timers/promises';
import { after, before, test } from 'node:test';

// Isolated transport fixtures only. No real session, data store or provider.
const LIMIT = 1_048_576;
const primary = 'test-primary-not-an-issued-session';
const elevated = 'test-stepup-not-an-issued-session';
const cookie = `axignal-admin-session=${primary}; axignal-admin-stepup=${elevated}; axignal-customer-stepup=${elevated}`;
const reads = [
  ['/api/admin/marketing-pool', { enabled: false }],
  ['/api/admin/pilot-test-accounts', { a: '', b: '', revision: 0, authorizedForTest: false, savedBy: null, savedAt: null }],
  ['/api/admin/customer-access', { asOf: '2026-10-15T00:00:00Z', limit: 500, pilotEnabled: false, customers: [], accountOperations: { customers: [] }, pilot: null }],
  ['/api/admin/staff-capacity?tenantId=tenant_transport', { tenantId: 'tenant_transport', entitlementSource: 'UNKNOWN', activeStaffCapacity: 0, grants: [], audit: [] }],
];
let upstream, next, base, nextLog = '', calls = [], proofs = [];
let scenario = { status: 200, body: { enabled: false } };

before(async () => {
  upstream = http.createServer((request, response) => {
    if (request.url === '/internal/admin/step-up/verify') {
      proofs.push({ primary: request.headers.authorization, elevated: request.headers['x-axignal-step-up'] });
      request.resume();
      response.writeHead(204).end();
      return;
    }
    const chunks = [];
    request.on('data', chunk => chunks.push(chunk));
    request.on('end', () => {
      const text = Buffer.concat(chunks).toString('utf8');
      let body = null;
      try { body = text ? JSON.parse(text) : null; } catch { body = text; }
      calls.push({ method: request.method, path: request.url, authorization: request.headers.authorization, body });
      response.writeHead(scenario.status, { 'Content-Type': scenario.type ?? 'application/json' });
      response.end(typeof scenario.body === 'string' ? scenario.body : JSON.stringify(scenario.body));
    });
  }).listen(0, '127.0.0.1');
  await once(upstream, 'listening');
  const probe = http.createServer().listen(0, '127.0.0.1');
  await once(probe, 'listening');
  const port = probe.address().port;
  await new Promise(resolve => probe.close(resolve));
  base = `http://127.0.0.1:${port}`;
  next = spawn(process.execPath, ['node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1', '--port', String(port)], {
    cwd: process.cwd(), env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1',
      AXIGNAL_RUNTIME_ORIGIN: `http://127.0.0.1:${upstream.address().port}`, AXIGNAL_EXPERIENCE_ORIGIN: base },
    stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true,
  });
  for (const stream of [next.stdout, next.stderr]) stream.on('data', chunk => { nextLog = (nextLog + chunk).slice(-4000); });
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (next.exitCode !== null) throw new Error(`Next exited before readiness: ${nextLog}`);
    try {
      const response = await fetch(base + '/api/admin/projections/command', { signal: AbortSignal.timeout(1000) });
      await response.arrayBuffer();
      if (response.status === 401) return;
    } catch { /* bounded readiness retry; no authenticated request */ }
    await pause(200);
  }
  throw new Error(`Next did not become ready: ${nextLog}`);
}, { timeout: 45_000 });

after(async () => {
  if (next && next.exitCode === null) {
    const exited = once(next, 'exit');
    next.kill();
    await exited;
  }
  if (upstream) {
    upstream.closeAllConnections();
    await new Promise(resolve => upstream.close(resolve));
  }
});

async function request(path, options = {}, authenticated = true) {
  const response = await fetch(base + path, { ...options,
    headers: { ...(authenticated ? { Cookie: cookie } : {}), ...options.headers }, signal: AbortSignal.timeout(15_000) });
  const body = await response.json();
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(JSON.stringify(body).includes(primary), false);
  assert.equal(JSON.stringify(body).includes(elevated), false);
  return { status: response.status, body };
}
function configure(body, status = 200, type = 'application/json') { scenario = { body, status, type }; calls = []; proofs = []; }

test('unauthenticated Admin reads never reach the upstream', async () => {
  for (const [path] of reads) {
    configure({ enabled: false });
    const result = await request(path, {}, false);
    assert.equal(result.status, 401);
    assert.equal(calls.length, 0);
  }
});

for (const [path, valid] of reads) {
  test(`${path}: valid read retains the owning schema`, async () => {
    configure(valid);
    const result = await request(path);
    assert.equal(result.status, 200);
    assert.deepEqual(result.body, valid);
    assert.equal(calls.length, 1);
  });
  test(`${path}: malformed upstream JSON is 502, not invalid user input`, async () => {
    configure('{');
    const result = await request(path);
    assert.equal(result.status, 502);
    assert.equal(calls.length, 1);
  });
  test(`${path}: oversized upstream JSON fails closed`, async () => {
    configure(JSON.stringify({ ...valid, padding: 'x'.repeat(LIMIT) }));
    const result = await request(path);
    assert.equal(result.status, 502);
    assert.equal('padding' in result.body, false);
  });
}

const writes = [
  ['/api/admin/marketing-pool', { domain: 'transport.example', action: 'DISCARD' }, 1024],
  ['/api/admin/pilot-test-accounts', { a: '', b: '', expectedRevision: 0 }, 2048],
  ['/api/admin/customer-access/issue', { reason: 'Transport test only', inviteHours: 1, idempotencyKey: 'transport-test-command' }, 4096],
  ['/api/admin/staff-capacity/revoke', { grantRef: 'staff_capacity_0123456789abcdef', reason: 'Transport test only' }, 4096],
];
for (const [path, valid, limit] of writes) {
  test(`${path}: cross-origin and oversized commands do not reach the owning service`, async () => {
    configure({});
    const post = body => ({ method: 'POST', headers: { Origin: base, 'Content-Type': 'application/json' }, body });
    const denied = await request(path, { ...post(JSON.stringify(valid)), headers: { Origin: 'https://foreign.invalid', 'Content-Type': 'application/json' } });
    assert.equal(denied.status, 403);
    assert.equal(calls.length, 0);
    const oversized = await request(path, post(JSON.stringify(valid) + ' '.repeat(limit)));
    assert.equal(oversized.status, 413);
    assert.equal(oversized.body.reason, 'BODY_LIMIT');
    assert.equal(calls.length, 0);
    const malformed = await request(path, post('{'));
    assert.equal(malformed.status, 400);
    assert.equal(calls.length, 0);
  });
}
test('marketing command limits UTF-8 bytes, not JavaScript character count', async () => {
  const body = JSON.stringify({ action: 'CREATE_CAMPAIGN', name: 'é'.repeat(80), personas: Array(8).fill('é'.repeat(40)), countries: Array(40).fill('ES'), target: 1, endsOn: null });
  assert.ok(body.length <= 1024);
  assert.ok(Buffer.byteLength(body) > 1024);
  configure({ enabled: false });
  const result = await request('/api/admin/marketing-pool', { method: 'POST', headers: { Origin: base, 'Content-Type': 'application/json' }, body });
  assert.equal(result.status, 413);
  assert.equal(calls.length, 0);
});

test('upstream denial does not expose arbitrary reason text', async () => {
  configure({ reason: 'private-upstream-detail-not-for-browser' }, 403);
  const result = await request('/api/admin/marketing-pool');
  assert.equal(result.status, 403);
  assert.equal(JSON.stringify(result.body).includes('private-upstream-detail'), false);
});

test('known authorization denial survives an unreadable error body', async () => {
  for (const [path] of reads) {
    for (const status of [401, 403]) {
      configure('<html>no private details</html>', status);
      const result = await request(path);
      assert.equal(result.status, status);
    }
  }
});

const revoked = { grantRef: 'staff_capacity_0123456789abcdef', tenantId: 'tenant_transport', destination: 'CUSTOMER_ACCOUNT', capacity: 1, reason: 'Transport test only', grantedBy: 'admin_transport', grantedAt: '2026-10-01T00:00:00Z', expiresAt: '2026-11-01T00:00:00Z', revokedAt: '2026-10-15T00:00:00Z', revokedBy: 'admin_transport', revocationReason: 'Transport test only', state: 'REVOKED', provenance: 'STAFF_GRANT_NOT_BILLING' };
const writeResults = [reads[0][1], reads[1][1], { inviteRef: 'invite_transport', inviteToken: 't'.repeat(43), expiresAt: '2026-10-16T00:00:00Z', capacity: 1 }, { grant: revoked, entitlementSource: 'UNKNOWN' }];
for (const [index, [path, body]] of writes.entries()) {
  test(`${path}: valid command keeps its payload and existing credential boundary`, async () => {
    configure(writeResults[index]);
    const result = await request(path, { method: 'POST', headers: { Origin: base, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    assert.equal(result.status, 200);
    assert.deepEqual(result.body, writeResults[index]);
    assert.equal(calls.length, 1);
    assert.deepEqual(calls[0].body, body);
    const sensitive = index >= 2;
    assert.equal(calls[0].authorization, 'Bearer ' + (sensitive ? elevated : primary));
    assert.deepEqual(proofs, sensitive ? [{ primary: 'Bearer ' + primary, elevated: 'Bearer ' + elevated }] : []);
  });
}
test('customer and staff commands still require their independent step-up cookie', async () => {
  for (const [path, body] of writes.slice(2)) {
    configure({});
    const result = await request(path, { method: 'POST', headers: { Origin: base, 'Content-Type': 'application/json', Cookie: `axignal-admin-session=${primary}` }, body: JSON.stringify(body) });
    assert.equal(result.status, 403);
    assert.equal(calls.length, 0);
    assert.equal(proofs.length, 0);
  }
});
test('documented marketing refusal codes retain their meaning', async () => {
  for (const [reason, status] of [['STATE_CHANGED', 409], ['INVALID_MARKETING_POOL', 400], ['MARKETING_POOL_UNAVAILABLE', 503]]) {
    configure({ reason }, status);
    const result = await request('/api/admin/marketing-pool');
    assert.equal(result.status, status);
    assert.equal(result.body.reason, reason);
  }
});
test('JSON and legacy projections preserve unknown and remove unrequested authority metadata', async () => {
  const payload = { mode: 'ADMIN', currentSlug: 'command-center', commandCenter: { metrics: [{ metricId: 'mrr', value: null, completeness: 'UNKNOWN' }] }, principalId: 'must-not-leave-BFF', roles: ['FOUNDER'] };
  const escaped = JSON.stringify(payload).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  for (const [body, type] of [[payload, 'application/json'], [`<div id="admin-bootstrap" hidden>${escaped}</div>`, 'text/html']]) {
    configure(body, 200, type);
    const result = await request('/api/admin/projections/command');
    assert.equal(result.status, 200);
    assert.deepEqual(result.body, { mode: payload.mode, currentSlug: payload.currentSlug, commandCenter: payload.commandCenter });
    assert.equal(calls[0].path, '/admin/command-center');
  }
});
test('corrupt or oversized legacy projections stay unavailable without forwarding HTML', async () => {
  for (const body of ['<div>missing bootstrap</div>', `<div id="admin-bootstrap" hidden>${'x'.repeat(LIMIT)}</div>`]) {
    configure(body, 200, 'text/html');
    const result = await request('/api/admin/projections/command');
    assert.equal(result.status, 502);
    assert.deepEqual(result.body, { reason: 'ADMIN_READ_UNAVAILABLE' });
  }
});
