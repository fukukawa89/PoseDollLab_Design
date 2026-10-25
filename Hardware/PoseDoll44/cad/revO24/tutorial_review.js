async (page) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.reload();await page.waitForFunction(()=>window.O24_TUTORIAL_STATE?.ready);
  const setTime=async t=>{
    await page.locator('#timeline').evaluate((e,t)=>{e.value=String(Math.round(t*1000));e.dispatchEvent(new Event('input',{bubbles:true}))},t);
    await page.waitForFunction(t=>Math.abs(window.O24_TUTORIAL_STATE.time-Math.round(t*1000)/1000)<1e-8&&!window.O24_TUTORIAL_STATE.playing,t);
  };
  const read=()=>page.evaluate(()=>window.O24_TUTORIAL_STATE);
  const chapter=async id=>{await page.locator(`[data-chapter="${id}"]`).click();await page.waitForFunction(id=>window.O24_TUTORIAL_STATE.chapter===id,id)};
  const mode=async id=>{await page.locator(`[data-mode="${id}"]`).click();await page.waitForFunction(id=>window.O24_TUTORIAL_STATE.mode===id,id)};
  const diff=(a,b)=>{a=a.flat();b=b.flat();if(a.length!==b.length||![...a,...b].every(Number.isFinite))throw Error('Invalid numeric comparison');return Math.max(...a.map((v,i)=>Math.abs(v-b[i])))};
  const chapters=['elbow','forearm','wrist','shoulder','clavicle','whole'],cases=[],fkSamples=[];
  const neutral=await (await page.request.get(new URL('../profiles/pose_frames.json',page.url()).href)).json();
  const frameNames=await page.evaluate(()=>Object.fromEntries(window.O24.parts.map(p=>[p.name,p.frame])));
  // All 18 chapter/mode combinations, including every assembled mesh transform.
  for(const id of chapters){
    await chapter(id);await mode('rotate');await setTime(0);
    const choices=await page.locator('[data-motion]').evaluateAll(es=>es.map(e=>e.dataset.motion));
    for(const motion of choices){
      await page.locator(`[data-motion="${motion}"]`).click();await setTime(0);const start=await read();
      for(const time of[.25,.75]){
        await setTime(time);const r=await read();if(!r.ready||r.geometryParts!==124||r.manufacturingRelease)throw Error('Bad model state');
        if(diff(start.axis.origin,r.axis.origin)>1e-8)throw Error('Selected rotation axis origin drift: '+motion);
        if(motion==='forearm_roll'&&diff(start.frames.wrist_base.slice(0,12).filter((_,i)=>i%4===3),r.frames.wrist_base.slice(0,12).filter((_,i)=>i%4===3))>1e-8)throw Error('Forearm wrist center drift');
        if(id!=='whole')fkSamples.push({chapter:id,motion,time,angles:r.angles,frames:r.frames});
      }
    }
    if(id==='elbow'){await setTime(.25);await page.screenshot({path:'output/playwright/o24-tutorial-rotation.png'})}
    if(id==='forearm'){await setTime(.25);await page.screenshot({path:'output/playwright/o24-tutorial-forearm.png'})}
    if(id==='wrist'){await setTime(.25);await page.screenshot({path:'output/playwright/o24-tutorial-wrist.png'})}
    await mode('explode');await setTime(0);const closed=await read();
    for(const p of closed.parts)if(diff(p.matrix,neutral.neutral[frameNames[p.name]])>1e-8)throw Error('Explode zero differs from source neutral');
    await setTime(1);const exploded=await read();
    if(!exploded.parts.some((p,i)=>diff(p.matrix,closed.parts[i].matrix)>1))throw Error('No explosion movement: '+id);
    if(id==='elbow'||id==='shoulder'||id==='whole')await page.screenshot({path:`output/playwright/o24-tutorial-${id}-exploded.png`});
    await mode('assemble');await setTime(0);let previous=-1;
    const steps=[];
    for(let step=0;step<=6;step++){
      if(step>0){await page.getByRole('button',{name:'下一步 →',exact:true}).click();await page.waitForFunction(t=>Math.abs(window.O24_TUTORIAL_STATE.time-t)<1e-7,step/6)}
      const r=await read(),assembled=r.parts.filter(p=>p.separation<1e-8).length;
      if(assembled<previous)throw Error('Assembly count went backwards');previous=assembled;steps.push(assembled);
      if(step===3&&id==='elbow')await page.screenshot({path:'output/playwright/o24-tutorial-assembly.png'});
    }
    const assembled=await read(),frames=await page.evaluate(()=>Object.fromEntries(window.O24.parts.map(p=>[p.name,p.frame])));
    for(const p of assembled.parts)if(diff(p.matrix,neutral.neutral[frames[p.name]])>1e-8||p.separation!==0||p.opacity!==1)throw Error('Assembly endpoint mismatch '+p.name);
    cases.push({chapter:id,parts:assembled.parts.length,motions:choices,assemblyStepCounts:steps,allPartsReturnToOriginalTransforms:true});
  }
  // Test actual clock-driven playback, pause, speed and stepping through UI controls.
  await chapter('elbow');await mode('rotate');await setTime(0);
  await page.getByRole('button',{name:'播放动画',exact:true}).click();
  await page.waitForFunction(()=>window.O24_TUTORIAL_STATE.time>.025);
  await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForFunction(()=>!window.O24_TUTORIAL_STATE.playing);
  const paused=(await read()).time;await page.waitForTimeout(160);if((await read()).time!==paused)throw Error('Pause did not freeze animation');
  await page.getByRole('combobox',{name:'播放速度'}).selectOption('0.5');await page.getByRole('button',{name:'播放动画',exact:true}).click();
  await page.waitForFunction(t=>window.O24_TUTORIAL_STATE.time>t+.005,paused);await page.getByRole('button',{name:'暂停动画',exact:true}).click();
  await page.getByRole('checkbox',{name:'零件标签',exact:true}).uncheck();await page.locator('#labels').waitFor({state:'hidden'});await page.getByRole('checkbox',{name:'零件标签',exact:true}).check();await page.locator('#labels').waitFor({state:'visible'});
  await page.getByRole('button',{name:'认识零件：轴承',exact:true}).click();if(!(await page.locator('#part-info').textContent()).includes('内外圈'))throw Error('Part teaching text absent');
  await page.getByRole('button',{name:'正面',exact:true}).click();await page.getByRole('button',{name:'侧面',exact:true}).click();await page.getByRole('button',{name:'复位',exact:true}).click();
  await page.setViewportSize({width:390,height:844});await setTime(.25);await page.screenshot({path:'output/playwright/o24-tutorial-mobile.png',fullPage:true});
  const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,canvasWidth:document.querySelector('canvas').clientWidth}));if(mobile.scrollWidth>mobile.width+1||mobile.canvasWidth<300)throw Error('Mobile overflow');
  await page.setViewportSize({width:1440,height:1000});
  const links=await page.locator('a').evaluateAll(es=>es.map(e=>e.href));for(const link of links){const r=await page.request.head(link);if(r.status()!==200)throw Error('Broken link '+link)}
  if(errors.length)throw Error(errors.join('\n'));
  return {status:'PASS',chapters:cases,kinematicSamples:fkSamples,playbackPausePassed:true,mobile,checkedLinks:links.length,errors};
}
