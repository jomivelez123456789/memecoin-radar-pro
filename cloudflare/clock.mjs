// Optional scheduler only. No wallet, Telegram token, state key or financial data.
// It is NOT deployed by publishing this repository.
const REPOSITORY = 'jomivelez123456789/memecoin-radar-pro';
const ENDPOINT = `https://api.github.com/repos/${REPOSITORY}/actions/workflows/radar.yml/dispatches`;

export async function dispatch(env, request = fetch) {
  if (!env.GITHUB_DISPATCH_TOKEN || typeof env.GITHUB_DISPATCH_TOKEN !== 'string') {
    throw new Error('Falta o segredo limitado para iniciar a verificação.');
  }
  let response;
  try {
    response = await request(ENDPOINT, {
      method: 'POST', redirect: 'error',
      headers: {
        'Authorization': `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
        'User-Agent': 'MemecoinRadar-Clock',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ref: 'main', inputs: {initialize: false}}),
      signal: AbortSignal.timeout(15000),
    });
  } catch {
    // Do not log response bodies, headers or error objects with credentials.
    throw new Error('Não foi possível pedir a verificação ao GitHub.');
  }
  if (response.status !== 204) {
    throw new Error(`O GitHub não aceitou o pedido de verificação (HTTP ${response.status}).`);
  }
  return true;
}

export default {
  async scheduled(_event, env, _context) {
    await dispatch(env);
  },
  async fetch() {
    // No public endpoint that could trigger a job without authorization.
    return new Response('Sem acesso público.', {status: 404});
  },
};
