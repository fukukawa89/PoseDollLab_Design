async page => {
 const errors=[],badResponses=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('response',r=>{if(r.status()>=400)badResponses.push({url:r.url(),status:r.status()});});
 const root='http://127.0.0.1:8769';
 const response=await page.goto(root+'/tutorials/full-doll/index.html');
 await page.waitForFunction(()=>window.O13_READY===true);
 const viewer={url:page.url(),contentType:response.headers()['content-type'],title:await page.title()};
 viewer.sceneAudit=await page.evaluate(()=>{
  const t=O13_TEST,missing=[],counts={};
  for(const c of ['manny','quinn']){t.state.character=c;counts[c]=t.scenes().length;for(let i=0;i<t.scenes().length;i++){t.state.pose=i;for(const o of t.scenes()[i].objects)if(!O13_MODELS[o.key])missing.push(o.key);t.draw();}}
  return {missing,counts,glError:document.querySelector('canvas').getContext('webgl').getError(),facts:O13_RESULTS};
 });
 await page.selectOption('#character','quinn');
 const contactIndex=await page.evaluate(()=>O13_TEST.scenes().findIndex(s=>s.pose==='arms_crossed'));
 await page.selectOption('#pose',String(contactIndex));
 viewer.contactText=await page.locator('#coverage').innerText();
 await page.locator('#shoulders').click();
 await page.locator('.workbench').screenshot({path:'E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/output/playwright/o14-contact-view.png'});
 await page.locator('#core').click();
 await page.locator('#alpha').fill('20');await page.locator('#beta').fill('-60');
 viewer.core=await page.evaluate(()=>({parts:O13_CORE.length,alpha:O13_TEST.state.alpha,beta:O13_TEST.state.beta,enabled:O13_TEST.state.core}));
 await page.locator('.workbench').screenshot({path:'E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/output/playwright/o14-core-view.png'});
 await page.setViewportSize({width:390,height:844});
 viewer.mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
 const gr=await page.goto(root+'/bench/revO13/README.zh-CN.md');
 const guide={url:page.url(),contentType:gr.headers()['content-type'],title:await page.title()};
 await page.locator('.part img').first().waitFor({state:'visible'});
 await page.waitForFunction(()=>[...document.querySelectorAll('.part img')].every(x=>x.complete));
 guide.mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,images:[...document.querySelectorAll('.part img')].map(x=>x.complete&&x.naturalWidth>0),replacementCharacters:document.body.innerText.includes('\uFFFD'),parts:document.querySelectorAll('.part').length,bomRows:document.querySelectorAll('tbody tr').length}));
 await page.screenshot({path:'E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/output/playwright/o14-guide-mobile.png'});
 const hrefs=await page.locator('a').evaluateAll(xs=>xs.map(x=>x.href).filter(x=>x.startsWith(location.origin)));
 guide.links=[];for(const url of [...new Set(hrefs)]){const r=await page.request.get(url);guide.links.push({url,status:r.status()});}
 await page.setViewportSize({width:1440,height:1080});
 await page.goto(root+'/tutorials/core-print/index.html');
 return {viewer,guide,errors,badResponses};
}
