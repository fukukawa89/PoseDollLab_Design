async (page) => {
  const report={status:'PASS',errors:[],samples:[],links:[],checks:{}};
  page.on('pageerror',e=>report.errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')report.errors.push(m.text())});
  const settle=()=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  const get=()=>page.evaluate(()=>window.O24B_VIEW_STATE);
  const check=(ok,msg)=>{if(!ok)throw Error(msg)};
  const angle=async(f,d)=>{await page.locator('#flex').fill(String(f));await page.locator('#deviation').fill(String(d));await settle()};
  await page.setViewportSize({width:1500,height:1000});
  await page.goto('http://127.0.0.1:8775/preview/index.html');
  await page.waitForFunction(()=>window.O24B_VIEW_STATE?.ready);
  await page.locator('#zero').click();await settle();
  report.geometry_sha256=(await get()).geometry_sha256;
  for(const f of [-65,0,70])for(const d of [-20,0,30]){
    await angle(f,d);const s=await get();check(s.angles.wrist_flex===f&&s.angles.wrist_deviation===d,'range input mismatch');report.samples.push(s);
  }
  await angle(45,20);await page.screenshot({path:'output/playwright/o24b-wrist.png'});
  const atStart=await get();await page.locator('#explode').fill('100');await settle();
  const ex=await get();check(ex.explode===1&&!ex.playing&&ex.angles.wrist_flex===0&&await page.locator('#flex').isDisabled(),'explosion lock');
  await page.screenshot({path:'output/playwright/o24b-exploded.png'});
  await page.locator('#explode').fill('0');await settle();check(!(await page.locator('#flex').isDisabled()),'reassembly unlock');
  await angle(45,20);check(JSON.stringify((await get()).frames)===JSON.stringify(atStart.frames),'reassembly changes pose');report.checks.explosion_roundtrip=true;
  await page.locator('[data-mode="compare"]').click();await settle();
  check((await get()).mode==='compare'&&await page.locator('#compare-heads').isVisible(),'compare mode');
  check(!(await page.locator('#overlay').isVisible()),'stale wrist annotations in comparison');
  await page.locator('#xray').uncheck();await settle();await page.screenshot({path:'output/playwright/o24b-compare.png'});
  await page.locator('[data-mode="arm"]').click();
  await settle();check(!(await page.locator('#overlay').isVisible()),'stale wrist annotations in whole arm');
  for(const pose of ['neutral','bent','raised']){
    await page.locator('#pose').selectOption(pose);await settle();report.samples.push(await get());
  }
  await page.screenshot({path:'output/playwright/o24b-arm.png'});
  await page.locator('[data-mode="wrist"]').click();await page.locator('#xray').check();
  for(const motion of ['flex','deviation','combined']){
    await page.locator('#motion').selectOption(motion);
    await page.waitForFunction(()=>{const s=window.O24B_VIEW_STATE;return s.playing&&(Math.abs(s.angles.wrist_flex)>5||Math.abs(s.angles.wrist_deviation)>5)});
    const s=await get();check(s.playing,'animation not running');
    if(motion==='flex')check(s.angles.wrist_deviation===0,'flex anim affects deviation');
    if(motion==='deviation')check(s.angles.wrist_flex===0,'deviation anim affects flex');
    await page.locator('#play').click();await settle();const paused=await get();await settle();check(JSON.stringify(paused.angles)===JSON.stringify((await get()).angles),'pause drift');
  }
  report.checks.three_animations_and_pause=true;
  await page.locator('[data-view="front"]').click();await settle();check((await get()).camera.yaw===0,'front camera');
  await page.locator('[data-view="side"]').click();await settle();check(Math.abs((await get()).camera.yaw-Math.PI/2)<1e-9,'side camera');
  await page.locator('#fit').click();await page.locator('#zero').click();await settle();
  const box=await page.locator('#scene').boundingBox();const before=(await get()).camera;
  await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2+50,box.y+box.height/2+20);await page.mouse.up();await settle();
  check((await get()).camera.yaw!==before.yaw,'drag orbit');await page.mouse.wheel(0,-200);await settle();check((await get()).camera.zoom>1,'wheel zoom');report.checks.camera=true;
  const hrefs=await page.locator('a').evaluateAll(nodes=>nodes.map(n=>n.href));
  for(const url of [...new Set(hrefs)]){const response=await page.request.get(url);report.links.push({url,status:response.status()});check(response.ok(),'broken link '+url)}
  await page.setViewportSize({width:390,height:844});await page.locator('#fit').click();await settle();await page.evaluate(()=>window.scrollTo(0,0));
  report.checks.mobile_no_horizontal_overflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);check(report.checks.mobile_no_horizontal_overflow,'mobile overflow');
  await page.screenshot({path:'output/playwright/o24b-mobile.png'});
  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForFunction(()=>window.O24B_VIEW_STATE?.ready);check(!(await get()).playing,'reduced motion autoplay');report.checks.reduced_motion=true;
  await page.setViewportSize({width:1500,height:1000});await page.goto('file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24B/preview/index.html');
  await page.waitForFunction(()=>window.O24B_VIEW_STATE?.ready);check((await get()).geometry_sha256===report.geometry_sha256,'offline hash mismatch');report.checks.offline_file=true;
  report.checks.webgl_error=await page.evaluate(()=>document.querySelector('canvas').getContext('webgl').getError());check(report.checks.webgl_error===0,'WebGL error');
  check(report.errors.length===0,'browser errors '+report.errors);return report;
}
