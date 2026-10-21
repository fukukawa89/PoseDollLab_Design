async (page) => {
 const out = await page.evaluate(() => {
  const a=O22_ANIMATION;let sum={bindings:a.data.bind.length,chapters:a.data.chapters.length,actions:a.data.actions.length,matrices:0,maxFinalError:0,invalid:[]};
  for(const c of a.data.chapters){a.goto(c.end-1,{t:1});let m=a.getMatrices();for(let i of c.objects){sum.matrices++;let err=Math.max(...m[i].map((v,j)=>Math.abs(v-a.scene.objects[i].matrix[j])));sum.maxFinalError=Math.max(sum.maxFinalError,err);if(err>1e-5)sum.invalid.push({chapter:c.id,part:a.scene.objects[i].label,error:err})}}
  return sum;
 });
 return out;
}
