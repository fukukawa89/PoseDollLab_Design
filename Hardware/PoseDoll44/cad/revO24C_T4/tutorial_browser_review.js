async (page) => {
 const errors=[],states=[],orientationChecks=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.setViewportSize({width:1440,height:1050});await page.goto('http://127.0.0.1:8780/tutorial/index.html?v=assembly158#W-3');await page.waitForFunction(()=>window.inspectTutorial?.().ready);
 const initial=await page.evaluate(()=>inspectTutorial());if(initial.station!=='W'||initial.index!==2)throw Error('Deep link not retained');
 const meta=await page.evaluate(()=>({geo:LESSONS.geometry_sha256,edition:LESSONS.tutorial_edition,lessons:Object.fromEntries(Object.entries(LESSONS.lessons).map(([st,l])=>[st,l.steps]))}));
 let count=0,additions=0;
 const progress=async(value)=>page.locator('#progress').evaluate((e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}))},value);
 for(const st of ['H','R','W']){
  await page.locator('[data-station="'+st+'"]').click();
  for(let i=0;i<meta.lessons[st].length;i++){
   const step=meta.lessons[st][i];await page.locator('#stepSelect').selectOption(String(i));
   for(const t of [0,500,1000]){
    await progress(t);
    const result=await page.evaluate(()=>{
     const q=inspectTutorial(),s=LESSONS.lessons[q.station].steps[q.index];
     if(q.webglError||q.miniError)throw Error('WebGL '+q.station+'/'+q.index);
     if(document.querySelector('#instruction').textContent!==s.text)throw Error('Wrong text');
     if(['add','remove','reinstall'].includes(s.kind)){
      const p=LESSONS.catalog[s.ids[0]];
      if(document.querySelector('#partName').textContent!==p.label||document.querySelector('#spec').textContent!==p.spec)throw Error('Wrong hardware detail');
     }
     const expected=new Set(Object.keys(s.before));for(const id of Object.keys(s.paths))expected.add(id);
     if(s.kind==='remove'&&q.t===1)for(const id of s.ids)expected.delete(id);
     if([...expected].sort().join()!==q.shownIds.sort().join())throw Error('Visibility mismatch '+q.station+'/'+q.index);
     return {station:q.station,index:q.index,kind:q.kind,t:q.t,matrices:q.currentMatrices,rom:q.kind==='rom'?q.shownMatrices:null,angles:q.angles};
    });states.push(result);
   }
   if(step.kind==='add')additions++;count++;
  }
  // Representative images of real assemblies and disassembly paths.
  const index=st==='H'?meta.lessons.H.findIndex(s=>s.ids[0]==='HL_S2'):st==='R'?meta.lessons.R.findIndex(s=>s.kind==='move'):meta.lessons.W.findIndex(s=>s.kind==='rom');
  await page.locator('#stepSelect').selectOption(String(index));await progress(st==='R'?500:1000);await page.locator('#fit').click();
  await page.screenshot({path:'output/playwright/o24ct4-tutorial-'+st+'.png',fullPage:true});
 }
 // Verify actual rendered face colour, reversal controls and A8 directions.
 await page.locator('[data-station="H"]').click();
 for(const id of ['HL_F1','HL_N','HL_S1','HL_S2']){
  const i=meta.lessons.H.findIndex(s=>s.kind==='add'&&s.ids[0]===id);await page.locator('#stepSelect').selectOption(String(i));await progress(1000);
  const before=await page.evaluate(()=>({state:inspectTutorial().orientation,pixels:inspectHardwarePixels(),card:document.querySelector('#orientationCard').hidden,diagram:document.querySelector('#orientationSketch').textContent}));
  if(before.card||!before.state?.shown)throw Error('Orientation hidden '+id);
  if(id==='HL_F1'&&before.pixels.green<20)throw Error('Smooth face not rendered');
  if(id.includes('_S')&&!before.diagram.includes('内孔凸边相对'))throw Error('Missing spring diagram');
  await page.locator('#flipPart').click();const after=await page.evaluate(()=>inspectHardwarePixels());if(!after.flipped)throw Error('Flip broken');
  if(id==='HL_F1'&&after.green>=before.pixels.green)throw Error('Washer flip did not expose opposite face');
  await page.locator('#faceFocus').click();orientationChecks.push({id,before,after});
 }
 // Transport: autoplay must stop at a checkpoint rather than skip human verification.
 const nextCheck=meta.lessons.H.findIndex((s,i)=>i>5&&s.kind==='check'&&meta.lessons.H[i-1].kind==='add');
 await page.locator('#stepSelect').selectOption(String(nextCheck-1));await page.locator('#auto').check();await progress(990);await page.locator('#play').click();
 await page.waitForFunction(i=>{const q=inspectTutorial();return q.index===i&&q.kind==='check'&&!q.playing},nextCheck,{timeout:10000});
 const auto=await page.evaluate(()=>inspectTutorial());await page.locator('#auto').uncheck();
 await page.locator('#prev').click();if((await page.evaluate(()=>inspectTutorial())).index!==nextCheck-1)throw Error('Previous');
 await page.locator('#replay').click();await page.waitForFunction(()=>inspectTutorial().t>.03);await page.locator('#play').click();const paused=await page.evaluate(()=>inspectTutorial());if(paused.playing)throw Error('Pause');
 await page.locator('#next').click();if((await page.evaluate(()=>inspectTutorial())).index!==nextCheck)throw Error('Next');
 // Capture nonzero Y and X wrist poses independently, matching current CAD order.
 await page.locator('[data-station="W"]').click();await page.locator('#stepSelect').selectOption(String(meta.lessons.W.findIndex(s=>s.kind==='rom')));
 for(const t of [180,420,710,900]){await progress(t);const q=await page.evaluate(()=>inspectTutorial());states.push({station:q.station,index:q.index,kind:q.kind,t:q.t,matrices:q.currentMatrices,rom:q.shownMatrices,angles:q.angles})}
 await page.setViewportSize({width:390,height:844});await page.locator('#stepSelect').selectOption('32');await progress(500);
 const mobile=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,ready:inspectTutorial().ready,error:inspectTutorial().webglError}));if(mobile.overflow||mobile.error)throw Error('Mobile layout');
 await page.screenshot({path:'output/playwright/o24ct4-tutorial-mobile.png',fullPage:true});
 await page.goto('file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24C_T4/tutorial/index.html#R-18');await page.waitForFunction(()=>window.inspectTutorial?.().ready);
 const offline=await page.evaluate(()=>inspectTutorial());if(offline.station!=='R'||offline.index!==17||offline.webglError)throw Error('Offline');
 await page.setViewportSize({width:1440,height:1050});
 for(const name of ['HARDWARE','ONE_PRINT','START_HERE']){await page.goto('http://127.0.0.1:8780/'+name+'.html');await page.screenshot({path:'output/playwright/o24ct4-'+name.toLowerCase()+'-updated.png',fullPage:true})}
 return {passed:!errors.length,geometry_sha256:meta.geo,edition:meta.edition,steps:count,additions,states,orientationChecks,auto_stopped:!auto.playing&&auto.kind==='check',pause_worked:!paused.playing,mobile,offline:{ready:offline.ready,station:offline.station,index:offline.index,geometrySha:offline.geometrySha},errors};
}
