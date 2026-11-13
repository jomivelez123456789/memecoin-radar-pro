import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {dispatch} from './clock.mjs';

test('clock dispatches only the intended repository and never initializes state', async () => {
  await dispatch({GITHUB_DISPATCH_TOKEN: 'dummy'}, async (url, options) => {
    assert.equal(url, 'https://api.github.com/repos/jomivelez123456789/memecoin-radar-pro/actions/workflows/radar.yml/dispatches');
    assert.deepEqual(JSON.parse(options.body), {ref: 'main', inputs: {initialize: false}});
    assert.equal(options.redirect, 'error');
    assert.equal(options.headers.Authorization, 'Bearer dummy');
    return {status: 204};
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
