async (page) => {
  await page.waitForFunction(() => window.O22_ANIMATION_LAST_DRAW?.finite);
  await page.setViewportSize({width:1440,height:1000});
  const selections = await page.evaluate(() => {let a=O22_ANIMATION;return [0,8,a.data.actions.findIndex(x=>x.detail==='spring'),a.data.actions.findIndex(x=>x.overlay==='latch'),a.data.actions.findIndex(x=>x.kind==='wire'),a.data.actions.findIndex(x=>x.kind==='plug'),952,1637]});
  let result=[];
  for(const index of selections){await page.evaluate(i=>O22_ANIMATION.goto(i,{t:.55}),index);await page.locator('#model').screenshot({path:'o22f7_animation_'+index+'.png'});result.push(await page.evaluate(()=>O22_ANIMATION_LAST_DRAW));}
  await page.evaluate(()=>O22_ANIMATION.goto(0,{t:.5}));
  await page.screenshot({path:'o22f7_animation_desktop.png'});
  return result;
}
