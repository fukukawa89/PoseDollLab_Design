async page => {
  await page.locator('#pose').selectOption('arms_forward');
  await page.getByRole('button',{name:'播放检查路径'}).click();
  const started=await page.evaluate(()=>({pose:window.O24D_VIEW_STATE.pose,status:document.querySelector('#status').textContent}));
  await page.waitForFunction(()=>window.O24D_VIEW_STATE.pose==='arms_forward',{},{timeout:15000});
  const completed=await page.evaluate(()=>({pose:window.O24D_VIEW_STATE.pose,status:document.querySelector('#status').textContent,
    geometry_sha256:window.O24D.geometry_sha256,samples:window.O24D.paths.arms_forward.path.length,
    max_angle_difference_deg:Math.max(...window.O24D.profile.axes.map(a=>Math.abs((window.O24D_VIEW_STATE.angles[a.id]||0)-(window.O24D.poses.arms_forward.angles[a.id]||0))))}));
  await page.locator('#pose').selectOption('neutral');
  return {status:started.pose==='custom' && started.status.includes('已检查路径') && completed.max_angle_difference_deg<1e-9 ? 'PASS':'FAIL',
    geometry_sha256:completed.geometry_sha256,started,completed,scope:'Actual UI button playback from A neutral along stored sampled path to final named pose; no continuous collision proof.'};
}
