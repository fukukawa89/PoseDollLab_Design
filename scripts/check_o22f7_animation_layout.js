async (page) => {
 await page.reload();await page.waitForFunction(()=>window.O22_ANIMATION_LAST_DRAW?.finite);
 await page.setViewportSize({width:1440,height:1000});
 for (const index of [32,85,1487,1488,1635]){await page.evaluate(i=>O22_ANIMATION.goto(i,{t:.65}),index);await page.screenshot({path:'o22f7_animation_review_'+index+'.png'});}
 await page.setViewportSize({width:390,height:844});
 for(const index of [0,85,1488]){await page.evaluate(i=>O22_ANIMATION.goto(i,{t:.55}),index);await page.screenshot({path:'o22f7_animation_mobile_'+index+'.png',fullPage:true});}
 return await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,width:innerWidth,errors:O22_ANIMATION_LAST_DRAW}));
}
