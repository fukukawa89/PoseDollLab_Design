async (page) => {
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.setViewportSize({width:1280,height:1000});
  await page.reload();
  await page.waitForFunction(() => window.O12_READY === true);
  const count = await page.getByRole('combobox', {name:'高亮一个零件'}).locator('option').count();
  if (count !== 16) throw Error('Expected 15 parts plus all-parts option');
  await page.getByRole('combobox',{name:'高亮一个零件'}).selectOption('shoulder_D4_L8_M3_thread6');
  const label = await page.locator('#part-info').innerText();
  if (!label.includes('螺纹长 6') || !label.includes('扳手 3')) throw Error('Wrong shoulder screw label');
  const slider = page.getByRole('slider',{name:'拆开'});
  await slider.focus(); await slider.press('End');
  if (await slider.inputValue() !== '1') throw Error('Explosion slider failed');
  await page.getByRole('button',{name:'播放拆装示意'}).click();
  await page.waitForFunction(() => window.O12_TEST.state.e > .15 && window.O12_TEST.state.e < .85);
  await page.getByRole('button',{name:'暂停',exact:true}).click();
  if (await page.evaluate(() => window.O12_TEST.state.playing)) throw Error('Pause failed');
  await page.getByRole('combobox',{name:'高亮一个零件'}).selectOption('');
  await slider.focus(); await slider.press('End');
  await page.locator('.work').screenshot({path:'o12-exploded.png'});
  await slider.press('Home');
  await page.locator('.work').screenshot({path:'o12-assembled.png'});
  const pixels = await page.evaluate(() => {
    const c=document.querySelector('#model'), gl=c.getContext('webgl');
    if(!gl) return 0;
    const b=new Uint8Array(c.width*c.height*4);
    gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,b);
    let n=0; for(let i=4;i<b.length;i+=4) if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>25)n++;
    return n;
  });
  if(pixels<100) throw Error('Blank WebGL canvas');
  const [download] = await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'下载 O12 小样 · 3MF'}).click()]);
  if(download.suggestedFilename()!=='O12_taobao_bench.3mf') throw Error('Wrong print version');
  await download.saveAs('o12-downloaded.3mf');
  const links = await page.locator('a[href]').evaluateAll(els => els.map(el=>el.href).filter(h=>h.startsWith(location.origin)));
  const responses = [];
  for (const url of links) { const r=await page.request.get(url); responses.push({url,status:r.status()}); if(!r.ok())throw Error('Broken link '+url); }
  await page.screenshot({path:'o12-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.waitForFunction(() => document.querySelector('#model').clientWidth > 100);
  const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  if(mobile.scrollWidth>mobile.width+1)throw Error('Mobile overflow');
  await page.screenshot({path:'o12-mobile.png',fullPage:true});
  if(errors.length)throw Error(errors.join('\n'));
  return {status:'PASS',errors,partOptions:count,nonBackgroundPixels:pixels,mobile,downloadFilename:download.suggestedFilename(),responses,
    checks:['15 part meshes','6 mm screw and 3 mm key label','native explosion slider','animation advance and pause','nonblank WebGL','3MF download','local links','mobile layout'],
    physical_tested:false};
}