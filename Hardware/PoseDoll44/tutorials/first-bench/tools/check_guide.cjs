'use strict';
const {chromium}=require('C:/Users/Ding/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert'),{pathToFileURL,fileURLToPath}=require('url');
const root=path.resolve(__dirname,'..'),out=path.join(root,'verification');
const url=process.argv[2]||'http://127.0.0.1:8768/tutorials/first-bench/index.html';
fs.mkdirSync(out,{recursive:true});
let activeBrowser;
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 activeBrowser=browser;
 const errors=[],requests=[],checks=[];
 const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
 await context.addInitScript(()=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async t=>{window.TEST_COPIED=t;}}});});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 await page.goto(url);await page.waitForFunction(()=>window.BENCH_GUIDE_READY);
 const canvas=page.locator('#part-canvas');
 const image=()=>canvas.evaluate(c=>c.toDataURL());
 const baseline=await image();await canvas.focus();await page.keyboard.press('ArrowDown');assert.notStrictEqual(await image(),baseline);
 await page.click('#model-topview');assert.notStrictEqual(await image(),baseline);
 await page.click('#model-reset');
 await page.screenshot({path:path.join(out,'desktop-parts.png'),fullPage:true});
 const n=await page.locator('[data-part]').count();assert.strictEqual(n,6);
 const drawings=new Set(),labels=[];
 for(let i=0;i<n;i++){await page.click('[data-part="'+i+'"]');drawings.add(await image());labels.push(await page.locator('#part-info h2').innerText());assert((await page.locator('#part-info').innerText()).includes('至少'));}
 assert.strictEqual(drawings.size,6);checks.push('Six distinct rendered CAD/parametric models; keyboard rotation, top view and reset');
 await page.click('[data-part="2"]');await page.screenshot({path:path.join(out,'desktop-peek.png'),fullPage:true});
 await page.click('#model-spin');await page.waitForTimeout(200);assert.strictEqual(await page.locator('#model-spin').getAttribute('aria-pressed'),'true');
 let lessonViews=0;
 for(const id of ['spring','friction']){
  await page.click('[data-nav="'+id+'"]');await page.locator('#'+id).waitFor({state:'visible'});
  assert.strictEqual(await page.locator('#model-spin').getAttribute('aria-pressed'),'false');
  const types=id==='spring'?['B8','A8']:['LP6','M4'];
  for(const type of types){
   await page.click('[data-'+id+'="'+type+'"]');
   const steps=await page.locator('#'+id+'-steps button').count();
   for(let i=0;i<steps;i++){
    await page.click('#'+id+'-steps [data-step="'+i+'"]');
    await page.locator('#'+id+'-progress').evaluate(e=>{e.value='65';e.dispatchEvent(new Event('input',{bubbles:true}));});
    assert((await page.locator('#'+id+'-instruction').innerText()).includes('STEP '+String(i+1).padStart(2,'0')));
    assert((await page.locator('#'+id+'-svg').innerHTML()).length>1800);
    assert.strictEqual(await page.locator('#'+id+'-percent').innerText(),'65%');lessonViews++;
   }
  }
  await page.click('#'+id+'-steps [data-step="2"]');const initial=await page.locator('#'+id+'-svg').innerHTML();
  await page.click('#'+id+'-play');await page.waitForFunction(id=>Number(document.querySelector('#'+id+'-progress').value)>4,id);
  assert.notStrictEqual(await page.locator('#'+id+'-svg').innerHTML(),initial);
  await page.click('#'+id+'-play');let v=await page.locator('#'+id+'-progress').inputValue();await page.waitForTimeout(130);assert.strictEqual(await page.locator('#'+id+'-progress').inputValue(),v);
  await page.locator('#'+id+'-progress').evaluate(e=>{e.value='70';e.dispatchEvent(new Event('input',{bubbles:true}));});
  await page.screenshot({path:path.join(out,'desktop-'+id+'.png'),fullPage:true});
 }
 checks.push(lessonViews+' lesson/type/step views; playback actually moves, pause holds, scrubbing works');
 await page.click('#friction-steps [data-step="4"]');await page.locator('#friction-progress').evaluate(e=>{e.value='50';e.dispatchEvent(new Event('input',{bubbles:true}));});
 assert((await page.locator('#friction-svg').textContent()).includes('加速演示 30 / 60 s'));
 await page.click('#friction-steps [data-step="5"]');await page.click('#friction-next');await page.locator('#prepare').waitFor({state:'visible'});assert.strictEqual(new URL(page.url()).hash,'#prepare');
 await page.check('#shop-0');await page.reload();await page.waitForFunction(()=>window.BENCH_GUIDE_READY);assert(await page.isChecked('#shop-0'));
 for(const role of ['spring','shop','lab']){
  await page.selectOption('#brief-role',role);assert((await page.inputValue('#brief-text')).length>190);
  await page.click('#copy-brief');assert.strictEqual(await page.evaluate(()=>window.TEST_COPIED),await page.inputValue('#brief-text'));
 }
 await page.fill('#brief-text','我添加的测试问题');await page.selectOption('#brief-role','spring');await page.selectOption('#brief-role','lab');assert.strictEqual(await page.inputValue('#brief-text'),'我添加的测试问题');
 await page.click('#copy-shopping');assert((await page.evaluate(()=>window.TEST_COPIED)).includes('至少 12 片'));
 await page.evaluate(()=>{Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw Error('denied')}}});});
 await page.click('#copy-shopping');assert(await page.locator('#copy-dialog').isVisible());assert((await page.inputValue('#copy-fallback')).includes('至少 6 片'));await page.click('#close-copy');
 await page.selectOption('#brief-role','spring');await page.locator('#toast').waitFor({state:'hidden'});
 await page.screenshot({path:path.join(out,'desktop-prepare.png'),fullPage:true});
 const download=page.waitForEvent('download');await page.locator('#prepare a[download]').click();const d=await download;
 const file=await d.path();assert(fs.readFileSync(file).subarray(0,2).equals(Buffer.from('PK')));
 checks.push('Persistent preparation checklist; editable role-specific briefs; clipboard success/fallback; real ZIP download');
 const links=await page.locator('a[href]').evaluateAll(a=>a.map(x=>x.getAttribute('href')));
 for(const href of links){
  if(href.startsWith('#')||href.startsWith('https://'))continue;
  const res=await context.request.get(new URL(href,url).href);assert(res.ok(),'Broken local link: '+href);
 }
 await page.click('[data-nav="results"]');await page.click('.technical summary');assert((await page.locator('#screen-values').innerText()).includes('0.463'));
 await page.screenshot({path:path.join(out,'desktop-results.png'),fullPage:true});
 let responsive=0;
 for(const width of [390,768,1024,1440]){
  await page.setViewportSize({width,height:900});
  for(const id of ['parts','spring','friction','prepare','results']){
   await page.click('[data-nav="'+id+'"]');await page.locator('#'+id).waitFor({state:'visible'});
   assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),'Horizontal overflow '+width+'/'+id);responsive++;
  }
 }
 await page.setViewportSize({width:390,height:844});await page.click('[data-nav="parts"]');await page.screenshot({path:path.join(out,'mobile-parts.png'),fullPage:true});
 await page.click('[data-nav="friction"]');await page.click('#friction-steps [data-step="4"]');await page.locator('#friction-progress').evaluate(e=>{e.value='50';e.dispatchEvent(new Event('input',{bubbles:true}));});await page.screenshot({path:path.join(out,'mobile-friction.png'),fullPage:true});
 checks.push(responsive+' chapter/viewport width combinations without page overflow; mobile screenshots');
 // A completely offline file:// run, also with unavailable localStorage and reduced-motion.
 const offline=await browser.newContext({offline:true,reducedMotion:'reduce',viewport:{width:1200,height:900}});
 await offline.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw Error('blocked')}});});
 const local=await offline.newPage();local.on('pageerror',e=>errors.push(e.message));
 await local.goto(pathToFileURL(path.join(root,'index.html')).href);await local.waitForFunction(()=>window.BENCH_GUIDE_READY);
 assert.strictEqual(await local.locator('#model-spin').getAttribute('aria-pressed'),'false');
 await local.click('[data-nav="prepare"]');await local.check('#shop-1');assert((await local.locator('#storage-status').innerText()).includes('未允许保存'));
 await local.emulateMedia({media:'print'});await local.screenshot({path:path.join(out,'print-preview.png'),fullPage:true});
 checks.push('Offline direct-file startup; denied storage handled; reduced-motion starts paused; printable checklist');
 assert.deepStrictEqual(errors,[]);assert(requests.every(u=>!/^https?:/.test(u)||new URL(u).hostname==='127.0.0.1'),'Unexpected remote dependency');
 await browser.close();
 fs.writeFileSync(path.join(out,'browser-checks.json'),JSON.stringify({passed:true,checks,models:labels,lesson_views:lessonViews,responsive_views:responsive,errors,scope:'Frontend behavior only. No hardware measurement or qualification.'},null,2));
 console.log(JSON.stringify({passed:true,lessonViews,responsive,checks}));
})().catch(async e=>{if(activeBrowser)await activeBrowser.close();console.error(e);process.exit(1)});

