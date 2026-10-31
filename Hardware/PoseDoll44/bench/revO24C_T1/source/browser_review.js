async (page) => {
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));const rows=[];
  await page.goto('http://127.0.0.1:8777/preview/index.html');
  const geometrySha=await page.evaluate(()=>window.KIT.geometry_sha256);
  const revision=await page.evaluate(()=>window.KIT.revision);
  await page.setViewportSize({width:1440,height:1000});
  for(const station of ['H','R','W']){
    await page.locator('#station').selectOption(station);
    for(const edge of ['Home','End']){
      await page.locator('#angle').focus();await page.keyboard.press(edge);
      if(station==='W'){await page.locator('#dev').focus();await page.keyboard.press(edge);}
      rows.push(await page.evaluate(()=>({...window.inspectKit(),matrix:matrix(D.parts.find(p=>p.station===S.station&&p.frame!=='fixed'))})));
    }
  }
  await page.locator('#zero').click();await page.locator('#explode').focus();await page.keyboard.press('End');
  rows.push(await page.evaluate(()=>window.inspectKit()));
  await page.screenshot({path:'output/playwright/o24ct1-wrist-exploded.png'});
  await page.locator('#part').selectOption('W04');rows.push(await page.evaluate(()=>window.inspectKit()));
  for(const id of ['H04','H05','R04','R05']){
    await page.locator('#station').selectOption(id[0]);await page.locator('#part').selectOption(id);
    const state=await page.evaluate(()=>window.inspectKit());
    if(state.shown!==1)throw new Error('Isolated part not shown: '+id);
    rows.push({...state,part:id});
    if(id==='H04')await page.screenshot({path:'output/playwright/o24ct1-s2-h04.png'});
  }
  await page.locator('#station').selectOption('all');await page.locator('#zero').click();
  await page.screenshot({path:'output/playwright/o24ct1-overview.png'});
  await page.goto('http://127.0.0.1:8777/START_HERE.html');
  const links=await page.locator('a').evaluateAll(a=>a.map(x=>x.href));const checked=[];
  for(const url of [...new Set(links)].filter(u=>u.startsWith('http://127.0.0.1:8777/'))){const r=await page.request.head(url);checked.push({url,status:r.status()});}
  await page.screenshot({path:'output/playwright/o24ct1-start.png'});
  await page.goto('http://127.0.0.1:8777/REPRINT_S2.html');
  const repairLinks=await page.locator('a').evaluateAll(a=>a.map(x=>x.href));
  for(const url of [...new Set(repairLinks)].filter(u=>u.startsWith('http://127.0.0.1:8777/'))){const r=await page.request.head(url);checked.push({url,status:r.status()});}
  await page.screenshot({path:'output/playwright/o24ct1-s2-reprint.png'});
  await page.setViewportSize({width:390,height:844});await page.goto('http://127.0.0.1:8777/preview/index.html');
  const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,...window.inspectKit()}));
  await page.screenshot({path:'output/playwright/o24ct1-mobile.png'});
  await page.goto('file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24C_T1/preview/index.html');
  const offline=await page.evaluate(()=>window.inspectKit());
  await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:8777/preview/index.html');
  return {geometrySha,revision,errors,rows,checked,mobile,offline};
}
