async (page) => {
 const errors=[],rows=[],matrixSamples=[],checked=[],hardware=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.setViewportSize({width:1440,height:1080});
 await page.goto('http://127.0.0.1:8777/tutorial/index.html');
 await page.waitForFunction(()=>window.inspectTutorial?.().ready);
 const initial=await page.evaluate(()=>window.inspectTutorial());
 const meta=await page.evaluate(()=>({revision:window.LESSONS.revision,geometry:window.LESSONS.geometry_sha256,lessons:window.LESSONS.lessons,catalog:window.LESSONS.catalog}));
 const scrub=async value=>page.locator('#progress').evaluate((el,v)=>{el.value=String(v);el.dispatchEvent(new Event('input',{bubbles:true}))},value);
 for(const station of ['H','R','W']){
  await page.locator(`[data-station="${station}"]`).click();
  const lesson=meta.lessons[station];
  for(let i=0;i<lesson.steps.length;i++){
   const s=lesson.steps[i];await page.locator('#stepSelect').selectOption(String(i));await scrub(500);
   const state=await page.evaluate(()=>window.inspectTutorial());
   if(!state.ready||state.webglError||state.miniError||state.index!==i)throw Error('Bad step '+station+' '+i);
   if(s.kind==='add'){
    if(s.ids.length!==1)throw Error('Not one part: '+station+' '+i);
    const id=s.ids[0],p=meta.catalog[id],spec=await page.locator('#spec').innerText();
    if(spec!==p.spec||!state.shownIds.includes(id))throw Error('Bad part label: '+id);
    if(p.orientation){
     const o=p.orientation,title=await page.locator('#orientationTitle').innerText(),description=await page.locator('#orientationText').innerText();
     if(title!==o.title||description!==o.instruction||!state.orientation?.shown)throw Error('Missing face instruction: '+id);
     const pixels=await page.evaluate(()=>window.inspectHardwarePixels());
     if(o.kind==='nylon'&&pixels.blue<100)throw Error('Nylon ring not visible: '+id);
     if(o.kind==='washer'&&pixels.green<100)throw Error('Smooth face not visible: '+id);
     if(o.kind==='plain'&&pixels.blue!==0)throw Error('Plain nut painted as nylon: '+id);
     await page.locator('#flipPart').click();const reverse=await page.evaluate(()=>window.inspectHardwarePixels());
     if(!reverse.flipped||(o.kind==='washer'&&reverse.green!==0)||(o.kind==='nylon'&&reverse.blue>=pixels.blue))throw Error('Wrong reverse face: '+id);
     await page.locator('#flipPart').click();
     hardware.push({id,kind:o.kind,state,pixels,reverse});
     matrixSamples.push(state);
    }
   }
   if(s.posePaths||s.kind==='rom'||i===1)matrixSamples.push(state);
   await scrub(1000);const end=await page.evaluate(()=>window.inspectTutorial());
   if(Object.keys(s.after).sort().join()!==end.shownIds.sort().join())throw Error('Missing components '+station+' '+i);
   rows.push({station,index:i,kind:s.kind,shown:end.shownIds.length,webglError:end.webglError,miniError:end.miniError});
  }
  const final=await page.evaluate(()=>window.inspectTutorial());
  if(final.shownIds.length!==lesson.total_parts)throw Error('Final count '+station);
  await page.locator('#fit').click();await page.screenshot({path:`output/playwright/tutorial-${station}-complete.png`});
 }
 const faceScreens=[['H','Hshaft_clamp_nut_-1','tutorial-H-nylon.png'],['H','Hrotor_bolt_-20','tutorial-H15-plain.png'],['H','Hrotor_w_-20','tutorial-H-washer.png'],['R','Rshaft_clamp_nut_-1','tutorial-R-nylon.png'],['W','Wguide_w_-1','tutorial-W-guide-washer.png'],['W','Wliner_n_1_-8.5','tutorial-W-nylon.png']];
 for(const [station,id,name]of faceScreens){
  await page.locator(`[data-station="${station}"]`).click();const index=meta.lessons[station].steps.findIndex(s=>s.kind==='add'&&s.ids[0]===id);
  await page.locator('#stepSelect').selectOption(String(index));await scrub(500);
  if(id==='Hrotor_bolt_-20')await page.locator('#faceFocus').click();
  const state=await page.evaluate(()=>inspectTutorial());if(state.webglError||state.miniError)throw Error('Face focus failed');
  await page.screenshot({path:'output/playwright/'+name,fullPage:true});
  await page.locator('#xray').uncheck();
 }
 await page.locator('[data-station="H"]').click();await page.locator('#stepSelect').selectOption('29');await scrub(500);await page.locator('#xray').check();
 await page.screenshot({path:'output/playwright/tutorial-H-preload.png',fullPage:true});
 await page.locator('#xray').uncheck();await page.locator('#prev').click();const previous=await page.evaluate(()=>window.inspectTutorial());
 if(previous.index!==28||previous.playing)throw Error('Previous failed');
 await page.locator('#next').click();const next=await page.evaluate(()=>window.inspectTutorial());if(next.index!==29)throw Error('Next failed');
 await page.locator('#replay').click();await page.waitForFunction(()=>window.inspectTutorial().t>.12);await page.locator('#play').click();const paused=await page.evaluate(()=>window.inspectTutorial());if(paused.playing)throw Error('Pause failed');
 await page.locator('#stepSelect').selectOption('10');await page.locator('#speed').selectOption('1.5');await page.locator('#auto').check();await page.locator('#play').click();
 await page.waitForFunction(()=>{const s=window.inspectTutorial();return s.index===11&&s.kind==='check'&&!s.playing},{},{timeout:15000});
 const checkpoint=await page.evaluate(()=>window.inspectTutorial());await page.locator('#auto').uncheck();
 await page.locator('[data-station="W"]').click();const wi=meta.lessons.W.steps.findIndex(s=>s.kind==='add'&&s.ids[0]==='W04');
 await page.locator('#stepSelect').selectOption(String(wi));await scrub(500);await page.screenshot({path:'output/playwright/tutorial-W-liner.png',fullPage:true});
 const links=await page.locator('a[href]').evaluateAll(a=>a.map(x=>x.href));
 for(const url of [...new Set(links)].filter(u=>u.startsWith('http://127.0.0.1:8777/'))){const r=await page.request.head(url);checked.push({url,status:r.status()});}
 await page.locator('[data-station="H"]').click();await page.locator('#stepSelect').selectOption('2');
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'output/playwright/tutorial-mobile.png',fullPage:true});
 const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,...window.inspectTutorial()}));
 await page.goto('file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24C_T1/tutorial/index.html#W-15');await page.waitForFunction(()=>window.inspectTutorial?.().ready);
 const offline=await page.evaluate(()=>window.inspectTutorial());
 await page.setViewportSize({width:1440,height:1080});await page.goto('http://127.0.0.1:8777/tutorial/index.html#H-30');await scrub(500);
 return {passed:errors.length===0,revision:meta.revision,geometrySha:meta.geometry,initial,errors,rows,matrixSamples,hardware,faceScreens,previous,next,paused,checkpoint,checked,mobile,offline};
}
