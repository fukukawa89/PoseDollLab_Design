async (page) => {
 await page.route('**/*',route=>route.continue());
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('http://127.0.0.1:14381/O22F7-3bb29f82690948a8a4be92768ea705ee/assembly/tutorials/assembly-o22/animation/index.html');await page.waitForFunction(()=>window.O22_ANIMATION_LAST_DRAW?.finite);await page.setViewportSize({width:1440,height:1000});
 let report={passed:false,console_errors:errors,tests:[],screenshots:[],final_pose_max_error_mm:0};
 const assert=(b,t)=>{if(!b)throw Error(t);report.tests.push(t)};
 await page.getByRole('combobox',{name:'装配章节',exact:true}).selectOption('S18');
 assert((await page.locator('#chapter-badge').textContent()).includes('左髋'),'章节跳转');
 await page.getByRole('searchbox',{name:'查找动作或零件',exact:true}).fill('P095');
 await page.locator('#step-list button.step').first().click();
 assert((await page.locator('#part-identity').textContent()).includes('D01-01 / P095'),'P095 当前盘位与动作');
 await page.getByRole('button',{name:'看它在哪一盘 ↗',exact:true}).click();
 await page.locator('#plate-image').evaluate(img=>img.decode());
 assert((await page.locator('#plate-title').textContent()).includes('D01-01'),'当前盘图入口');
 await page.locator('#plate-dialog [data-close]').click();await page.locator('#search').fill('');
 await page.evaluate(()=>O22_ANIMATION.goto(0));await page.getByRole('button',{name:'▶ 播放本步',exact:true}).click();await page.waitForFunction(()=>O22_ANIMATION.state.t>.16);await page.getByRole('button',{name:'Ⅱ 暂停',exact:true}).click();
 const t=await page.evaluate(()=>O22_ANIMATION.state.t);await page.waitForTimeout(150);assert(await page.evaluate(t=>O22_ANIMATION.state.t===t,t),'播放与暂停保持位置');
 await page.locator('#scrub').evaluate(el=>{el.value=600;el.dispatchEvent(new Event('input',{bubbles:true}))});assert(await page.evaluate(()=>Math.abs(O22_ANIMATION.state.t-.6)<1e-8),'拖动当前动作进度');
 await page.locator('#next').click();await page.locator('#prev').click();assert(await page.evaluate(()=>O22_ANIMATION.state.index===0),'上一动作与下一动作');
 await page.locator('#xray').check();await page.locator('#isolate').check();assert(await page.evaluate(()=>O22_ANIMATION.state.xray&&O22_ANIMATION.state.isolate),'内部显示与单件查看');await page.locator('#view-reset').click();
 await page.evaluate(()=>O22_ANIMATION.goto(0,{t:.99}));await page.locator('#play').click();await page.waitForFunction(()=>O22_ANIMATION.state.t===1&&!O22_ANIMATION.state.playing);assert(await page.evaluate(()=>O22_ANIMATION.state.index===0),'默认每步结束自动暂停');
 await page.locator('#mode').selectOption('watch');await page.evaluate(()=>O22_ANIMATION.seek(.99));await page.locator('#play').click();await page.waitForFunction(()=>O22_ANIMATION.state.index===1);await page.locator('#play').click();assert(await page.evaluate(()=>O22_ANIMATION.state.index===1),'连续观看自动前进');await page.locator('#mode').selectOption('follow');
 assert(await page.evaluate(()=>O22_ANIMATION.data.actions.every(a=>!a.needs_path_review)), '没有遗留的未完成装入动作');
 assert((await page.locator('#coverage-label').textContent()).includes('46 路电路'),'显示逐件与电路覆盖');
 const frames=await page.evaluate(()=>{let a=O22_ANIMATION,out={max:0,chapters:[]};for(const c of a.data.chapters){a.goto(c.end-1,{t:1});let m=a.getMatrices(),error=0;for(const i of c.objects)error=Math.max(error,...m[i].map((v,j)=>Math.abs(v-a.scene.objects[i].matrix[j])));out.max=Math.max(out.max,error);out.chapters.push({id:c.id,error,objects:c.objects.length})}return out});report.final_pose_max_error_mm=frames.max;report.chapter_frames=frames.chapters;assert(frames.max<1e-5,'26 章最终位置与发布模型一致');
 const picks=await page.evaluate(()=>{let a=O22_ANIMATION;let get=(label,fn)=>({label,index:a.data.actions.findIndex(fn)});return [get('pelvis',x=>x.new.some(i=>a.scene.objects[i].label==='frame/pelvis')),get('p095',x=>x.new.some(i=>a.scene.objects[i].label==='thigh_l/C14')),get('spring',x=>x.detail==='spring'),get('sensor',x=>x.overlay==='latch'),get('wire',x=>x.kind==='wire'),get('plug',x=>x.kind==='plug'),get('power',x=>x.kind==='power'),get('tie',x=>x.kind==='tie'),get('finished',x=>x.kind==='finished'),get('left_root',x=>x.new.some(i=>O22_ANIMATION.scene.objects[i].print_id==='W005A')),get('right_clavicle',x=>x.new.some(i=>O22_ANIMATION.scene.objects[i].print_id==='H008')),get('left_join',x=>x.new.some(i=>O22_ANIMATION.scene.objects[i].print_id==='W005B'))]});
 for(const p of picks){await page.evaluate(i=>O22_ANIMATION.goto(i,{t:.63}),p.index);await page.screenshot({path:'o22f7_c7_'+p.label+'_final.png'});report.screenshots.push('o22f7_c7_'+p.label+'_final.png')}
 const rigid=await page.evaluate(()=>{const a=O22_ANIMATION;const root=a.scene.objects.findIndex(o=>o.print_id==='W005A'),park=a.data.actions.findIndex(x=>x.verified_path==='park_left_root');a.goto(park,{t:1});const M=a.getMatrices()[root].slice();a.goto(park+1,{t:0});return{error:Math.max(...M.map((v,j)=>Math.abs(v-a.getMatrices()[root][j]))),count:a.data.actions.filter(x=>x.pose_path).length}});assert(rigid.error<1e-7&&rigid.count>20,'左根部转开后在下一动作保持位置');
 await page.locator('#search').fill('W005A');await page.locator('#step-list button.step').first().click();await page.locator('#plate-open').click();await page.locator('#plate-image').evaluate(img=>img.decode());assert((await page.locator('#plate-title').textContent()).includes('D15-01'),'新根部对应新增 D15 盘图');await page.locator('#plate-dialog [data-close]').click();await page.locator('#search').fill('');
 await page.locator('#inventory-open').click();assert((await page.locator('#inventory-content').textContent()).includes('D07-05 / P242'),'量规与七个小样单独解释');await page.locator('#inventory-dialog [data-close]').click();
 const plug=picks.find(p=>p.label==='plug');await page.evaluate(i=>O22_ANIMATION.goto(i),plug.index);await page.reload();await page.waitForFunction(()=>window.O22_ANIMATION_LAST_DRAW?.finite);assert(await page.evaluate(i=>O22_ANIMATION.state.index===i,plug.index),'重新打开恢复观看位置');
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>O22_ANIMATION.seek(.5));await page.screenshot({path:'o22f7_c7_mobile_final.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'390 像素手机无横向溢出');report.screenshots.push('o22f7_c7_mobile_final.png');
 await page.locator('#circuit-size').click();assert(await page.locator('#circuit-panel').evaluate(el=>el.classList.contains('large')),'手机放大电路图');await page.locator('#circuit-size').click();
 await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>O22_ANIMATION.goto(0));
 const base='http://127.0.0.1:14381/O22F7-3bb29f82690948a8a4be92768ea705ee/';
 await page.goto(base+'assembly/tutorials/assembly-o22/index.html');await page.locator('#find').fill('W005A');assert(await page.locator('#parts tbody tr:visible').count()===1,'当前清单搜索新根部');assert((await page.locator('#parts tbody tr:visible').textContent()).includes('D15-01'),'清单与新盘位一致');await page.screenshot({path:'o22f7_c7_catalog_final.png'});report.screenshots.push('o22f7_c7_catalog_final.png');
 for(const id of ['W005A','W005B']){await page.goto(base+'index.html?id='+id);await page.waitForFunction(id=>document.querySelector('#title')?.textContent.startsWith(id),id);assert((await page.locator('#title').textContent()).includes(id),'实际打印网格载入 '+id);assert(await page.locator('#elbow-link').isHidden(),'拆分件不显示不适用的转角对比 '+id);assert((await page.locator('#notice').textContent()).includes('装配修订版 r4'),'当前已检查版本 '+id);await page.screenshot({path:'o22f7_c7_print_'+id+'.png'});report.screenshots.push('o22f7_c7_print_'+id+'.png');if(id==='W005B')assert((await page.locator('#stem-info').textContent()).includes('接合沉孔'),'明确标出新增孔位清理要求')}
 await page.goto(base+'assembly/tutorials/assembly-o22/animation/index.html');await page.waitForFunction(()=>window.O22_ANIMATION_LAST_DRAW?.finite);await page.evaluate(()=>O22_ANIMATION.goto(0));
 report.passed=errors.length===0;return report;
}
