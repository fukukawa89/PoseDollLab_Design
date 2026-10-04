const {chromium}=require('C:/Users/Ding/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve('Hardware/PoseDoll44');
const viewerUrl=process.argv[2]||'http://127.0.0.1:8874/generated/revO/RevO_Design_Review.html';
const out=path.resolve(process.argv[3]||path.join(root,'verification/revO/browser'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const page=await browser.newPage({viewport:{width:1320,height:1020},deviceScaleFactor:1});
 const errors=[],requests=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))requests.push({url:r.url(),status:r.status()})});
 await page.goto(viewerUrl);
 await page.waitForSelector('#sizeTable tr');
 if(await page.locator('#sizeTable tr').count()!==5)throw Error('Expected five candidate comparisons');
 await page.screenshot({path:path.join(out,'manny_480.png'),fullPage:true});
 checks.push({view:'manny480',text:await page.locator('#layoutDetail').innerText()});
 await page.selectOption('#character','quinn');await page.selectOption('#height','420');
 if(!(await page.locator('#layoutDetail').innerText()).includes('35.3'))throw Error('Wrong Quinn 420 deficit');
 await page.click('#side');await page.screenshot({path:path.join(out,'quinn_420_side.png'),fullPage:true});
 await page.click('[data-tab="joint"]');await page.waitForSelector('#jointDetail a');
 for(const family of ['S4','M6','L6']){
  await page.selectOption('#family',family);
  await page.waitForFunction(f=>document.querySelector('#jointDetail h2')?.textContent===f,family);
  checks.push({view:family,text:await page.locator('#jointDetail').innerText()});
  for(const a of await page.locator('#jointDetail a').all()){
   const href=await a.getAttribute('href');const response=await page.request.head(new URL(href,page.url()).href);if(!response.ok())throw Error('Missing joint review artifact '+href);
  }
 }
 await page.selectOption('#family','M6');await page.waitForFunction(()=>document.querySelector('#jointDetail h2')?.textContent==='M6');
 await page.check('#hideCase');await page.screenshot({path:path.join(out,'M6_internal.png'),fullPage:true});
 await page.check('#explode');await page.screenshot({path:path.join(out,'M6_exploded.png'),fullPage:true});
 await page.click('[data-tab="evidence"]');
 for(const a of await page.locator('#evidence a').all()){
  const href=await a.getAttribute('href');const response=await page.request.head(new URL(href,page.url()).href);if(!response.ok())throw Error('Missing linked artifact '+href);
 }
 await page.setViewportSize({width:390,height:844});await page.click('[data-tab="layout"]');
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
 if(overflow||errors.length||requests.length)throw Error(JSON.stringify({overflow,errors,requests}));
 await page.selectOption('#character','manny');await page.selectOption('#height','480');
 await browser.close();
 fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify({status:'PASS',errors,requests,overflow,checks,source_sha256:{
 'generated/revO/RevO_Design_Review.html':sha(path.join(root,'generated/revO/RevO_Design_Review.html')),
 'generated/revO/layout_data.json':sha(path.join(root,'generated/revO/layout_data.json')),
 'verification/revO/joint_study.json':sha(path.join(root,'verification/revO/joint_study.json'))
 }},null,2));
 console.log(JSON.stringify({status:'PASS',views:checks.length,errors,requests,overflow}));
})().catch(e=>{console.error(e);process.exit(1)});
