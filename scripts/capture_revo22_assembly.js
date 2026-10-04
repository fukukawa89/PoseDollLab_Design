async (page) => {
  await page.getByRole('button', { name: '查看本步可旋转 CAD / 单件识别 ↗' }).first().click();
  await page.waitForFunction(() => !!window.O22_ASSEMBLY_LAST_DRAW);
  const steps = await page.getByRole('combobox', { name: '装配步骤', exact: true }).locator('option').evaluateAll(options => options.map(o => o.value));
  for (const id of steps) {
    await page.getByRole('combobox', { name: '装配步骤', exact: true }).selectOption(id);
    await page.waitForFunction(id => window.O22_ASSEMBLY_LAST_DRAW.step === id, id);
    await page.getByLabel('可旋转三维关节模型', { exact: true }).screenshot({ path: 'Hardware/PoseDoll44/tutorials/assembly-o22/images/' + id + '.png' });
  }
  return { captured: steps.length, steps, last: await page.evaluate(() => window.O22_ASSEMBLY_LAST_DRAW) };
}
