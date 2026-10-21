async (page) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('http://127.0.0.1:8237/preview/index.html?revision=O23I-b9ef73123469');
  await page.waitForFunction(()=>window.O23_VIEW_STATE?.ready);
  const identity=await page.evaluate(()=>({revision:O23.review.revision,sha:O23.review.geometry_sha256,objects:O23.items.length,stls:O23.review.stl_count,status:document.querySelector('.status').innerText}));
  if(identity.sha!=='b9ef731234695c69dcfb250b7fc7a6bb65f9498bbaab62fd2b6939a2fc1fd818')throw Error('Stale viewer');
  const poses=await page.locator('#pose option').evaluateAll(es=>es.map(e=>e.value));
  for(const p of poses){await page.locator('#pose').selectOption(p);if(!await page.locator('#message').innerText().then(s=>s.startsWith('相邻干涉 0 条')))throw Error('Pose check '+p);}
  await page.locator('#pose').selectOption('A');
  await page.screenshot({path:'Hardware/PoseDoll44/bench/revO23/design/unified_candidate/images/preview_full.png'});
  await page.locator('#part').selectOption('frame/pelvis');
  if(await page.locator('#part-download').isVisible())throw Error('Unverified pelvis print offered');
  await page.locator('[data-view=front]').click();
  await page.screenshot({path:'Hardware/PoseDoll44/bench/revO23/design/unified_candidate/images/preview_pelvis.png'});
  await page.locator('#harness').check();await page.locator('#section').check();
  await page.locator('#section').uncheck();await page.locator('#harness').uncheck();
  await page.locator('#part').selectOption('frame/thigh_l');
  if(!await page.locator('#part-download').isVisible())throw Error('Verified thigh print missing');
  const urls=await page.locator('aside a').evaluateAll(es=>es.map(e=>e.href));
  for(const u of urls){const r=await page.request.head(u);if(r.status()!==200)throw Error('Link failed '+u+' '+r.status());}
  await page.locator('#reset').click();
  if(errors.length)throw Error(errors.join('\n'));
  return {identity,poses:poses.length,links:urls.length,errors};
}
