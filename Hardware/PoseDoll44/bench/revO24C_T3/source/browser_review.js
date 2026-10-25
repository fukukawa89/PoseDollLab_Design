async (page) => {
 const errors=[],states=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.setViewportSize({width:1440,height:1080});await page.goto('http://127.0.0.1:8779/viewer/index.html');await page.waitForFunction(()=>window.inspectKit?.().ready);
 const meta=await page.evaluate(()=>({geometry:KIT.geometry_sha256,steps:KIT.steps,parts:KIT.parts.map(p=>({id:p.id,spec:p.spec,note:p.note}))}));
 let initial=await page.evaluate(()=>inspectKit());if(initial.visible.length!==100||initial.webglError||initial.overflow)throw Error('Initial state '+JSON.stringify(initial));
 await page.screenshot({path:'output/playwright/o24ct3-installed.png',fullPage:true});states.push(initial);
 for(let i=0;i<meta.steps.length;i++){
  await page.locator('#step').selectOption(String(i));let s=await page.evaluate(()=>inspectKit());
  if(s.step!==i||s.webglError||s.overflow)throw Error('Step '+i);
  let details=await page.locator('#info').innerText(),txt=await page.locator('#stepInfo').innerText();if(!txt.includes(meta.steps[i].text))throw Error('Step text');
  for(let id of meta.steps[i].ids){let p=meta.parts.find(p=>p.id===id);if(!s.visible.includes(id)||!details.includes(id)||p.spec&&!details.includes(p.spec)||p.note&&!details.includes(p.note))throw Error('Part detail '+id)}
 }
 const set=async(id,v)=>page.locator('#'+id).evaluate((e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}))},v);
 for(let mode of ['H','R','W']){
  await page.locator('#mode').selectOption(mode);await page.locator('#bench').check();let s=await page.evaluate(()=>inspectKit());if(!s.visible.includes('F3-'+mode))throw Error('Missing load tool');states.push(s);
  if(mode==='H'){await set('q',145)}if(mode==='R'){await set('r',-85)}if(mode==='W'){await set('w',70);await set('v',30)}
  states.push(await page.evaluate(()=>inspectKit()));await page.screenshot({path:'output/playwright/o24ct3-'+mode+'-bench.png',fullPage:true});
  await set('explode',70);if((await page.evaluate(()=>inspectKit())).webglError)throw Error('Explode');await set('explode',0);
 }
 await page.locator('#mode').selectOption('arm');await page.getByRole('button',{name:'中立姿态',exact:true}).click();
 for(let[q,r,w,v]of[[0,0,0,0],[145,0,0,0],[145,-85,-65,-20],[145,80,70,30]]){
  for(let[id,n]of[['q',q],['r',r],['w',w],['v',v]])await set(id,n);let s=await page.evaluate(()=>inspectKit());if(s.angles.join()!==[q,r,w,v].join()||s.webglError||s.overflow)throw Error('Arm pose');states.push(s)
 }
 await page.getByRole('button',{name:'屈肘145°',exact:true}).click();await page.screenshot({path:'output/playwright/o24ct3-fold145.png',fullPage:true});
 await page.locator('#mode').selectOption('W');await page.locator('#bench').uncheck();await page.locator('#part').selectOption('Wball_nut_-5.5');await page.locator('#only').check();let only=await page.evaluate(()=>inspectKit());if(only.visible.join()!=='Wball_nut_-5.5')throw Error('Isolation');
 await page.setViewportSize({width:390,height:844});await page.locator('#step').selectOption('3');let mobile=await page.evaluate(()=>inspectKit());if(mobile.overflow||mobile.webglError)throw Error('Mobile overflow');await page.screenshot({path:'output/playwright/o24ct3-mobile.png',fullPage:true});
 await page.goto('file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24C_T3/viewer/index.html');await page.waitForFunction(()=>window.inspectKit?.().ready);let offline=await page.evaluate(()=>inspectKit());if(offline.webglError||offline.visible.length!==100)throw Error('Offline');
 await page.setViewportSize({width:1440,height:1080});await page.goto('http://127.0.0.1:8779/START_HERE.html');await page.screenshot({path:'output/playwright/o24ct3-entry.png',fullPage:true});
 return {passed:!errors.length,geometry_sha256:meta.geometry,errors,steps:meta.steps.length,states,mobile,offline,only};
}
