async (page) => {
  await page.reload();
  await page.locator('img').evaluateAll(es=>Promise.all(es.map(e=>e.decode())));
  await page.locator('.gallery').scrollIntoViewIfNeeded();
  await page.locator('.gallery').screenshot({path:'Hardware/PoseDoll44/bench/revO23/design/unified_candidate/images/gallery.png'});
  return await page.locator('img').evaluateAll(es=>es.map(e=>({src:e.getAttribute('src'),ok:e.complete&&e.naturalWidth>0})));
}
