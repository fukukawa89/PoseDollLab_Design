from pathlib import Path
H=Path('Hardware/PoseDoll44'); old=H/'tutorials/print-first'; new=H/'tutorials/taobao-bench'
app=(old/'app.js').read_text(encoding='utf-8')
app=app.replace('O11_','O12_').replace("shoulder_SBSM_M3_4_8:68","shoulder_D4_L8_M3_thread6:68")
app=app.replace("for(const n of ['bench','core'])","for(const n of ['bench'])")
app=app.replace("$('#core').onclick=()=>tab('core');","")
app=app.replace("先用它测打印材料的保持力、摆动阻力和长期受压变化。测试不需要购买整个人偶的电子器件。","两半底座一起换 O12；已打印的 O11 长臂可以复用。先检查金属垫圈实际能否套入，再装配加载。")
start=app.index("const r=window.O12_RESULTS;")
end=app.index("addEventListener('resize'",start)
app=app[:start]+"""const r=window.O12_RESULTS;$('#facts').innerHTML=[['名义零件配对',r.pairChecks+' × '+r.stackCases,'4种堆叠高度，未发现穿插'],['长臂角度抽样',r.motionCases+' 个状态','5°步长；不等于连续公差认证'],['实物配合与弹力','待到货测试','零间隙不能直接判定滑动配合']].map(x=>'<div class="fact">'+x[0]+'<strong>'+x[1]+'</strong><span>'+x[2]+'</span></div>').join('');$('#scope').textContent='本页只对应 O12 独立小样。尚未实际打印、确认金属孔径配合或测得碟簧弹力；没有据此放行完整关节或整个人偶。';
""" +app[end:]
(new/'app.js').write_text(app,encoding='utf-8')
css=(old/'style.css').read_text(encoding='utf-8')
css+='\n.arrival{background:#e7eadf;border:1px solid #c8d0c1;border-radius:12px;padding:28px}.arrival-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.arrival-grid b{display:block;margin-bottom:10px}.arrival-grid p{font-size:14px}.arrival .small{margin-top:12px}.arrival h2{max-width:700px}@media(max-width:700px){.arrival-grid{grid-template-columns:1fr;gap:12px}.arrival{padding:20px}.arrival-grid p{margin-bottom:6px}}\n'
(new/'style.css').write_text(css,encoding='utf-8')
