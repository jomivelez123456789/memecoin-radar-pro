import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {dispatch} from './clock.mjs';

test('clock dispatches only the intended repository and never initializes state', async () => {
  for (const status of [200, 204]) await dispatch({GITHUB_DISPATCH_TOKEN: 'dummy'}, async (url, options) => {
    assert.equal(url, 'https://api.github.com/repos/jomivelez123456789/memecoin-radar-pro/actions/workflows/radar.yml/dispatches');
    assert.deepEqual(JSON.parse(options.body), {ref: 'main', inputs: {initialize: false}});
    assert.equal(options.redirect, 'manual');
    assert.equal(options.headers.Authorization, 'Bearer dummy');
    assert.equal(options.headers['X-GitHub-Api-Version'], '2026-03-10');
    return {status};
  });
});
test('missing credentials do not send any request', async () => {
  await assert.rejects(dispatch({}, () => {throw new Error('unexpected request');}));
});
test('network and authorization errors never include the secret or body', async () => {
  const secret = 'private-example';
  for (const fetcher of [async () => {throw new Error(secret);}, async () => ({status: 403, body: secret})]) {
    try {await dispatch({GITHUB_DISPATCH_TOKEN: secret}, fetcher); assert.fail('must reject');}
    catch (error) {assert.equal(error.message.includes(secret), false);}
  }
});
test('public HTTP handler cannot start a run', async () => {
  assert.equal((await worker.fetch()).status, 404);
});
test('redirects are rejected after one request without forwarding credentials', async () => {
  for (const status of [301, 302, 303, 307, 308]) {
    let calls = 0;
    await assert.rejects(dispatch({GITHUB_DISPATCH_TOKEN: 'dummy'}, async (_url, options) => {
      calls++;
      assert.equal(options.redirect, 'manual');
      return {status, headers: new Headers({Location: 'https://example.org/untrusted'})};
    }), new RegExp(`HTTP ${status}`));
    assert.equal(calls, 1);
  }
});
