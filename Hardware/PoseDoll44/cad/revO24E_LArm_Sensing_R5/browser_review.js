async (page) => {
  await page.goto('http://127.0.0.1:8772/assembly_guide/index.html');
  await page.waitForFunction(() => window.GUIDE_API?.check().ready);
  const guide = await page.evaluate(async () => {
    const errors=[];const D=window.ARM_GUIDE;
    for(let i=0;i<D.steps.length;i++){
      GUIDE_API.setStep(i);
      for(const t of [0,.5,1]) {
        GUIDE_API.setProgress(t);
        const s=GUIDE_API.check();
        if(s.errors.length||s.scene_gl_error||s.detail_gl_error||s.step!==i+1)errors.push({i,t,s});
      }
      if(i%25===0)await new Promise(requestAnimationFrame);
    }
    for(const p of D.parts){GUIDE_API.inspect(p.id,false);if(GUIDE_API.check().detail_gl_error)errors.push({part:p.id});}
    GUIDE_API.setStep(0);GUIDE_API.setProgress(1);
    return {steps:D.steps.length,geometry_sha256:D.geometry_sha256,parts_inspected:D.parts.length,sampled_progress:[0,.5,1],errors};
  });
  await page.screenshot({path:'output/playwright/r5-guide.png'});
  await page.goto('http://127.0.0.1:8772/preview/index.html');
  await page.waitForFunction(() => window.O24D_VIEW_STATE?.ready);
  const viewer=await page.evaluate(()=>{
    const issues=[];for(const p of document.querySelector('#pose').options){
      if(p.disabled)continue;
      document.querySelector('#pose').value=p.value;document.querySelector('#pose').dispatchEvent(new Event('change'));
      const s=window.O24D_VIEW_STATE;if(s.visible===0||!s.ready)issues.push(p.value);
    }
    document.querySelector('#zero').click();
    let manual=0;
    for(const input of document.querySelectorAll('#sliders input[type=range]')) {
      for(const v of [input.min,'0',input.max]){input.value=v;input.dispatchEvent(new Event('input'));manual++;if(O24D_VIEW_STATE.pose!=='custom')issues.push('manual '+input.id);}
    }
    document.querySelector('#zero').click();
    document.querySelector('#harness').checked=true;document.querySelector('#harness').dispatchEvent(new Event('change'));
    return {...window.O24D_VIEW_STATE,errors:issues,manual_slider_checks:manual,webgl_error:document.querySelector('#view').getContext('webgl').getError(),sliders:document.querySelectorAll('#sliders input[type=range]').length,status:document.querySelector('#status').textContent};
  });
  await page.screenshot({path:'output/playwright/r5-viewer-wiring.png'});
  await page.selectOption('#focus','wrist');
  await page.uncheck('#harness');
  await page.screenshot({path:'output/playwright/r5-wrist.png'});
  await page.goto('http://127.0.0.1:8772/START_HERE.html');
  await page.screenshot({path:'output/playwright/r5-start.png',fullPage:true});
  return {passed:!guide.errors.length&&!viewer.errors.length&&!viewer.webgl_error&&viewer.sliders===7,guide,viewer};
}

