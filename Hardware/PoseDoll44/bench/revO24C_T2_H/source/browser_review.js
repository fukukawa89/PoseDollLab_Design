async (page) => {
 const errors=[],states=[],shots=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.setViewportSize({width:1440,height:1080});await page.goto('http://127.0.0.1:8778/viewer/index.html');await page.waitForFunction(()=>window.inspectH2?.().ready);
 const meta=await page.evaluate(()=>({steps:window.H2.steps,parts:window.H2.parts.map(p=>({id:p.id,spec:p.spec,note:p.note})),geometry:window.H2.geometry_sha256}));
 const scrub=async n=>page.getByRole('slider',{name:'本步进度'}).evaluate((e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}))},n);
 for(let i=0;i<meta.steps.length;i++){
  await page.getByRole('combobox',{name:'选择装配步骤'}).selectOption(String(i));
  const title=await page.locator('#title').innerText(),text=await page.locator('#instruction').innerText();if(title!==meta.steps[i].title||text!==meta.steps[i].text)throw Error('Text mismatch '+i);
  const card=await page.locator('#parts').innerText();for(let id of meta.steps[i].ids){let p=meta.parts.find(p=>p.id===id);if(!card.includes(id)||p.spec&&!card.includes(p.spec)||!card.includes(p.note))throw Error('Missing specification '+id)}
  for(let t of [0,500,1000]){await scrub(t);const s=await page.evaluate(()=>window.inspectH2());if(!s.ready||s.webglError||s.step!==i+1||s.overflow)throw Error('Bad state '+i);states.push(s)}
 }
 const final=await page.evaluate(()=>window.inspectH2());if(final.visible.length!==17)throw Error('Incomplete assembly');
 for(let [step,name]of [[4,'ordinary-nut'],[5,'cap-assembly'],[17,'opposed-springs'],[19,'shoulder-screw']]){
  await page.getByRole('combobox',{name:'选择装配步骤'}).selectOption(String(step-1));await scrub(500);await page.screenshot({path:`output/playwright/o24ct2h-${name}.png`,fullPage:true});shots.push(name)
 }
 await page.getByRole('button',{name:'播放本步',exact:true}).click();await page.waitForTimeout(250);let playing=await page.evaluate(()=>window.inspectH2());if(!playing.playing)throw Error('Play failed');await page.getByRole('button',{name:'暂停',exact:true}).click();let stopped=await page.evaluate(()=>window.inspectH2());await page.waitForTimeout(150);let still=await page.evaluate(()=>window.inspectH2());if(still.playing||still.progress!==stopped.progress)throw Error('Pause failed');
 await page.getByRole('combobox',{name:'选择装配步骤'}).selectOption('14');await page.getByRole('button',{name:'看本件朝向 / 翻面'}).click();const only=await page.evaluate(()=>window.inspectH2());if(only.visible.join()!=='F02')throw Error('Isolate failed');await page.getByRole('button',{name:'看本件朝向 / 翻面'}).click();
 await page.getByRole('combobox',{name:'查看方式'}).selectOption('assembled');
 for(let q of [-45,0,145,165]){await page.getByRole('slider',{name:'转动角度'}).evaluate((e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}))},q);let s=await page.evaluate(()=>window.inspectH2());if(s.angle!==q||s.visible.length!==17||s.webglError)throw Error('ROM failed');states.push(s)}
 await page.screenshot({path:'output/playwright/o24ct2h-rom.png',fullPage:true});
 await page.getByRole('combobox',{name:'查看方式'}).selectOption('exploded');states.push(await page.evaluate(()=>window.inspectH2()));await page.screenshot({path:'output/playwright/o24ct2h-exploded.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.getByRole('combobox',{name:'选择装配步骤'}).selectOption('16');let mobile=await page.evaluate(()=>window.inspectH2());if(mobile.overflow||mobile.webglError)throw Error('Mobile failed');await page.screenshot({path:'output/playwright/o24ct2h-mobile.png',fullPage:true});
 await page.goto('file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24C_T2_H/viewer/index.html#17');await page.waitForFunction(()=>window.inspectH2?.().ready);let offline=await page.evaluate(()=>window.inspectH2());if(offline.step!==17||offline.webglError)throw Error('Offline failed');
 await page.setViewportSize({width:1440,height:1080});await page.goto('http://127.0.0.1:8778/START_HERE.html');await page.screenshot({path:'output/playwright/o24ct2h-entry.png',fullPage:true});
 return {passed:errors.length===0,errors,geometry_sha256:meta.geometry,states,final,playing,stopped,mobile,offline,shots,steps:meta.steps.length};
}
