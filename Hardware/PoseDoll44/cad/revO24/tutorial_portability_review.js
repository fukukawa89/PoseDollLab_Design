async (page) => {
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await page.waitForFunction(()=>window.O24_TUTORIAL_STATE?.ready);
  const reduced=await page.evaluate(()=>window.O24_TUTORIAL_STATE.playing);if(reduced)throw Error('Reduced motion autoplay');
  await page.goto('http://127.0.0.1:8774/preview/index.html');await page.waitForFunction(()=>window.O24_VIEW_STATE?.ready);
  await page.getByRole('link',{name:/关节是怎样转起来的/}).click();await page.waitForFunction(()=>window.O24_TUTORIAL_STATE?.ready);
  const offline='file:///E:/UnrealProjects/PoseDollLab_UE58_Design/PoseDoll_HW44_Plan/design/Hardware/PoseDoll44/bench/revO24/preview/tutorial.html';
  await page.goto(offline);await page.waitForFunction(()=>window.O24_TUTORIAL_STATE?.ready);
  await page.locator('[data-chapter="whole"]').click();await page.locator('[data-mode="explode"]').click();
  await page.locator('#timeline').focus();await page.locator('#timeline').press('End');await page.waitForFunction(()=>window.O24_TUTORIAL_STATE.time===1);
  const offlineState=await page.evaluate(()=>({parts:window.O24_TUTORIAL_STATE.parts.length,mode:window.O24_TUTORIAL_STATE.mode,time:window.O24_TUTORIAL_STATE.time,error:document.querySelector('#error').textContent}));
  if(offlineState.parts!==124||offlineState.mode!=='explode'||offlineState.error)throw Error('Offline viewer failed');
  await page.goto('http://127.0.0.1:8774/preview/tutorial.html');await page.emulateMedia({reducedMotion:'no-preference'});
  if(errors.length)throw Error(errors.join('\n'));
  return {status:'PASS',reducedMotionStartsPaused:true,previewLinkWorks:true,offlineFileProtocol:offlineState,noExternalAssetDependency:true,errors};
}
