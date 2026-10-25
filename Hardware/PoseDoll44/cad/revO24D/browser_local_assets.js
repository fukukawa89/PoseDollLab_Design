async page => {
 const requests = [], external = [];
 const handler = async route => {
  const url = route.request().url(); requests.push(url);
  if (new URL(url).origin === 'http://127.0.0.1:8788') await route.continue();
  else { external.push(url); await route.abort(); }
 };
 await page.route('**/*', handler);
 try {
  await page.goto('http://127.0.0.1:8788/preview/index.html');
  await page.waitForFunction(() => window.O24D_VIEW_STATE && window.O24D_VIEW_STATE.visible > 0);
  const state = await page.evaluate(() => ({
   geometry_sha256: window.O24D.geometry_sha256,
   parts: window.O24D.parts.length,
   visible: window.O24D_VIEW_STATE.visible,
   pose: window.O24D_VIEW_STATE.pose,
   webgl_error: document.querySelector('#view').getContext('webgl').getError()
  }));
  return {status: external.length === 0 && state.parts === state.visible && state.webgl_error === 0 ? 'PASS' : 'FAIL',
   ...state, external_requests: external, local_requests: requests,
   scope: 'Reload actual preview with all non-loopback HTTP requests denied. Confirms bundled local assets; direct file: navigation is separately recorded as untested due to browser-tool restriction.'};
 } finally { await page.unroute('**/*', handler); }
}
