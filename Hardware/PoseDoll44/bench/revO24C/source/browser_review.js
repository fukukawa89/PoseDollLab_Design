async (page) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const pose=page.getByRole('combobox',{name:'查看动作'}),version=page.getByRole('combobox',{name:'对比版本'}),focus=page.getByRole('combobox',{name:'观察部位'});
  const choices=await pose.locator('option').evaluateAll(es=>es.filter(e=>!e.disabled).map(e=>e.value));
  const samples=[];
  for(const name of choices){
    await pose.selectOption(name);
    const r=await page.evaluate(()=>({state:window.O24_VIEW_STATE,status:document.querySelector('#status').textContent,error:document.querySelector('#error').textContent}));
    if(!r.state?.ready||r.state.parts!==113||!r.status.includes('交叠 0 对')||r.error)throw Error('Pose failed '+name);
    samples.push({pose:name,angles:r.state.angles,frames:r.state.frames});
  }
  await pose.selectOption('neutral');
  const before=await page.evaluate(()=>window.O24_VIEW_STATE.centers.wrist);
  if(!await page.locator('details').evaluate(el=>el.open))await page.locator('summary').click();
  const twist=page.getByRole('slider',{name:'前臂旋前 / 旋后'});
  await twist.focus();await twist.press('End');
  const after=await page.evaluate(()=>window.O24_VIEW_STATE.centers.wrist);const drift=Math.hypot(...after.map((v,i)=>v-before[i]));
  if(drift>1e-8)throw Error('Wrist orbital drift');
  if(!(await page.locator('#status').textContent()).includes('未做实体干涉验证'))throw Error('Custom false qualification');
  await pose.selectOption('neutral');await page.locator('summary').click();
  await page.getByRole('heading').scrollIntoViewIfNeeded();
  await page.locator('aside').evaluate(el=>el.scrollTop=0);
  await page.screenshot({path:'output/playwright/o24c-arm.png'});
  const comparisons=[];
  for(const group of ['shoulder','elbow','wrist']){
    await focus.selectOption(group);
    const cameraBefore=await page.evaluate(()=>({center:state.center,span:state.span,zoom:state.zoom}));
    await version.selectOption('O24B');
    if(!(await page.locator('#status').textContent()).includes('对比模型'))throw Error('B false qualification');
    const cameraAfter=await page.evaluate(()=>({center:state.center,span:state.span,zoom:state.zoom}));
    if(JSON.stringify(cameraBefore)!==JSON.stringify(cameraAfter))throw Error('Comparison changed camera scale');
    await page.screenshot({path:`output/playwright/o24c-${group}-B.png`});
    await version.selectOption('O24C');
    await page.screenshot({path:`output/playwright/o24c-${group}-C.png`});
    comparisons.push({group,same_camera:true,dimensions:await page.locator('#dimension-readout').textContent()});
  }
  await focus.selectOption('all');await pose.selectOption('elbow_max');
  await page.screenshot({path:'output/playwright/o24c-deep-fold.png'});
  await pose.selectOption('neutral');await page.getByRole('checkbox',{name:'显示整偶比例参考'}).check();
  await page.screenshot({path:'output/playwright/o24c-body-scale.png'});
  await page.getByRole('checkbox',{name:'显示整偶比例参考'}).uncheck();
  const links=await page.locator('nav a').evaluateAll(es=>es.map(e=>e.href));
  for(const link of links){const r=await page.request.head(link);if(r.status()!==200)throw Error('Broken link '+link)}
  const digest=await page.evaluate(()=>window.O24.geometry_sha256);
  if(errors.length)throw Error(errors.join('\n'));
  return {status:'PASS',samples,comparisons,forearm_twist_wrist_drift_mm:drift,geometry_sha256:digest,checked_links:links.length,errors};
}
