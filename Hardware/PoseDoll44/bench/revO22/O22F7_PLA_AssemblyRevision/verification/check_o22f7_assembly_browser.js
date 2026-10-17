async (page) => {
  const steps = await page.getByRole('combobox', { name: '装配步骤', exact: true }).locator('option').evaluateAll(os => os.map(o => o.value));
  if (steps.length !== 26) throw new Error('Expected 26 steps');
  const captures=[];
  for (const step of steps) {
    await page.getByRole('combobox', { name: '装配步骤', exact: true }).selectOption(step);
    await page.waitForFunction(id => window.O22_ASSEMBLY_LAST_DRAW?.step === id, step);
    const status=await page.evaluate(() => ({...window.O22_ASSEMBLY_LAST_DRAW}));
    if (status.objects < 1) throw new Error('Empty step '+step);
    await page.getByLabel('可旋转三维关节模型', {exact:true}).screenshot({path:'o22f7_assembly/'+step+'.png'});
    captures.push(status);
  }
  await page.getByRole('combobox', { name: '装配步骤', exact: true }).selectOption('S18');
  await page.getByRole('combobox', { name: '选择零件', exact: true }).selectOption('thigh_l/C14');
  await page.getByRole('checkbox', {name:'只看选中件',exact:true}).check();
  const p095=await page.locator('#view-part-info').textContent();
  const supportLink=await page.locator('#view-part-print').getAttribute('href');
  if (!p095.includes('D01-01') || !p095.includes('P095') || supportLink!=='../../../index.html?id=P095') throw new Error('P095 mapping mismatch');
  await page.locator('#viewer').screenshot({path:'o22f7_assembly/p095_current_body.png'});
  await page.getByRole('button',{name:'关闭 CAD 查看器',exact:true}).click();
  await page.locator('#part-search').fill('P130');
  const p130=await page.locator('.part-search-results tbody tr:visible').allTextContents();
  if (p130.length!==3 || p130.filter(s=>s.includes('可选小样')).length!==1) throw new Error('P130 instance/sample ambiguity');
  await page.locator('#part-search').fill('P095');
  if (await page.locator('.part-search-results tbody tr:visible').count()!==1) throw new Error('P095 search mismatch');
  await page.locator('#find-parts').scrollIntoViewIfNeeded();
  await page.screenshot({path:'o22f7_assembly/search_p095.png'});
  await page.locator('#part-search').fill('');
  const d01=page.locator('.plate-card').filter({has:page.locator('#plate-D01')});
  await d01.locator('summary').click();
  const labels=await d01.locator('tbody tr').allTextContents();
  if(labels.length!==12 || !labels[0].includes('D01-01 / P095') || !labels[2].includes('可选小样')) throw new Error('D01 card mismatch');
  await d01.screenshot({path:'o22f7_assembly/d01_card.png'});
  await page.locator('#wire-search').fill('A01');
  const wiring=await page.locator('#wire-table tbody tr:visible').allTextContents();
  if(wiring.length!==1 || !wiring[0].includes('A01')) throw new Error('Electrical A01 altered');
  await page.locator('#wire-search').fill('');
  await page.locator('#start').scrollIntoViewIfNeeded();
  await page.screenshot({path:'o22f7_assembly/desktop.png'});
  const bodyGeometry=await page.evaluate(()=>({revision:window.O22_ASSEMBLY.scene.revision,geometry:window.O22_ASSEMBLY.scene.geometry_url,printed:window.O22_ASSEMBLY.scene.objects.filter(o=>o.body_revision==='O22F7').length}));
  return {passed:true,captures,p095,supportLink,p130,d01Rows:labels.length,electricalA01Preserved:true,bodyGeometry};
}
