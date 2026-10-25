async (page) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const pose=page.getByRole('combobox',{name:'查看动作'});
  const choices=await pose.locator('option').evaluateAll(es=>es.filter(e=>!e.disabled).map(e=>e.value));
  const results=[];
  for(const choice of choices){
    await pose.selectOption(choice);
    const result=await page.evaluate(()=>({state:window.O24_VIEW_STATE,status:document.querySelector('#status').textContent,error:document.querySelector('#error').textContent}));
    if(!result.state?.ready||result.state.parts!==124||!result.status.includes('交叠 0 对')||result.error)throw Error('Pose failed: '+choice);
    results.push({pose:choice,centers:result.state.centers});
  }
  await pose.selectOption('neutral');
  const before=await page.evaluate(()=>window.O24_VIEW_STATE.centers.wrist);
  const twist=page.getByRole('slider',{name:'前臂旋前 / 旋后'});
  await twist.focus();await twist.press('End');
  const after=await page.evaluate(()=>window.O24_VIEW_STATE.centers.wrist);
  const drift=Math.hypot(...after.map((v,i)=>v-before[i]));
  if(drift>1e-8)throw Error('Wrist orbit drift '+drift);
  if(!(await page.locator('#status').textContent()).includes('未做实体干涉验证'))throw Error('Custom pose falsely marked qualified');
  await pose.selectOption('neutral');
  await page.getByRole('heading').scrollIntoViewIfNeeded();
  await page.getByRole('checkbox',{name:'显示整偶比例参考'}).check();
  await page.screenshot({path:'output/playwright/o24-body-scale.png'});
  await page.getByRole('checkbox',{name:'显示整偶比例参考'}).uncheck();
  await page.getByRole('button',{name:'正面',exact:true}).click();
  await page.screenshot({path:'output/playwright/o24-front.png'});
  await page.getByRole('button',{name:'立体',exact:true}).click();
  await page.screenshot({path:'output/playwright/o24-neutral.png'});
  await pose.selectOption('drink');
  await page.screenshot({path:'output/playwright/o24-drink.png'});
  await page.getByRole('checkbox',{name:'显示五金与传感板'}).uncheck();
  await page.getByRole('checkbox',{name:'显示五金与传感板'}).check();
  await pose.selectOption('neutral');
  const links=await page.locator('nav a').evaluateAll(es=>es.map(e=>e.href));
  for(const link of links){const response=await page.request.head(link);if(response.status()!==200)throw Error('Broken link '+link)}
  if(errors.length)throw Error(errors.join('\n'));
  return {status:'PASS',poses:results,forearm_endstop_wrist_drift_mm:drift,checked_links:links.length,errors};
}
