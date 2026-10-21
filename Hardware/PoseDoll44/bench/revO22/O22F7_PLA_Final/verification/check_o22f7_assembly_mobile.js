async (page) => {
  await page.locator('main img').evaluateAll(images=>images.forEach(img=>img.loading='eager'));
  const imageStatus=await page.locator('main img').evaluateAll(async images=>Promise.all(images.map(async img=>{await img.decode();return {src:img.getAttribute('src'),w:img.naturalWidth,h:img.naturalHeight}})));
  if(imageStatus.some(x=>x.w<1)) throw new Error('Image decode failure');
  await page.setViewportSize({width:390,height:844});
  await page.locator('#start').scrollIntoViewIfNeeded();
  const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  if(dimensions.scroll>dimensions.width+1) throw new Error('Mobile page overflow');
  await page.screenshot({path:'o22f7_assembly/mobile_intro.png'});
  await page.locator('#plate-D01').scrollIntoViewIfNeeded();
  await page.screenshot({path:'o22f7_assembly/mobile_d01.png'});
  await page.getByRole('button',{name:'查看本步三维装配 / 单件识别 ↗',exact:true}).first().click();
  await page.getByRole('combobox',{name:'装配步骤',exact:true}).selectOption('S24');
  await page.getByRole('combobox',{name:'选择零件',exact:true}).selectOption('foot_r/C14');
  await page.getByRole('checkbox',{name:'只看选中件',exact:true}).check();
  const foot=await page.locator('#view-part-info').textContent();
  if(!foot.includes('D11-02')||!foot.includes('P130'))throw new Error('Right foot mapping mismatch');
  await page.screenshot({path:'o22f7_assembly/mobile_model.png'});
  await page.getByRole('button',{name:'关闭 CAD 查看器',exact:true}).click();
  await page.setViewportSize({width:1500,height:1000});
  const card=page.locator('.plate-card').filter({has:page.locator('#plate-D01')});
  await card.screenshot({path:'o22f7_assembly/d01_card.png',style:'.contents{visibility:hidden}'});
  await page.goto('http://127.0.0.1:8778/assembly/tutorials/assembly-o22/index.html#plates');
  return {passed:true,imagesDecoded:imageStatus.length,mobile:dimensions,rightFoot:foot};
}
