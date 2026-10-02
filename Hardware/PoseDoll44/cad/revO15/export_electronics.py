"""Native KiCad fabrication export, conditional prototype only."""
from common import *
import subprocess,collections,shutil,csv
CLI=Path('D:/ProgramFiles/KiCad/10.0/bin/kicad-cli.exe')

def main():
 jobs=[('central_c1',H/'electronics/revO15/central_c1/PoseDoll_O15_Central_C1',4,1.2,1),('sensor_mini',H/'electronics/sensor_revC_mini/PoseDoll_AS5048A_revC_mini',2,1.,46)];reports=[]
 for tag,base,layers,thickness,quantity in jobs:
  dst=BENCH/'electronics'/tag;dst.mkdir(parents=True,exist_ok=True);pcb=base.with_suffix('.kicad_pcb');sch=base.with_suffix('.kicad_sch');inputs={str(p):sha(p) for p in [pcb,sch,base.with_suffix('.kicad_pro')]}
  cmds=[['sch','erc','--format','json','-o',str(dst/'erc.json'),str(sch)],['pcb','drc','--format','json','--schematic-parity','-o',str(dst/'drc.json'),str(pcb)]]
  for args in cmds:subprocess.run([str(CLI),*args],check=True)
  er=read(dst/'erc.json');dr=read(dst/'drc.json');ec=sum(len(s.get('violations',[])) for s in er.get('sheets',[]))
  if ec or dr['violations'] or dr['unconnected_items'] or dr.get('schematic_parity'):raise ValueError((tag,'check did not close'))
  for args in [['pcb','export','gerbers','--layers',','.join(['F.Cu']+(['In1.Cu','In2.Cu'] if layers==4 else [])+['B.Cu','F.Paste','B.Paste','F.Mask','B.Mask','F.Silkscreen','B.Silkscreen','Edge.Cuts']),'--output',str(dst/'gerbers'),str(pcb)],['pcb','export','drill','--excellon-units','mm','--excellon-separate-th','--output',str(dst/'gerbers'),str(pcb)],['pcb','export','pos','--format','csv','--units','mm','--smd-only','--output',str(dst/'placement.csv'),str(pcb)]]:subprocess.run([str(CLI),*args],check=True)
  comps=read(base.parent/'connectivity.json');groups={}
  for c in comps:
   if not c['fp']:continue
   key=(c['value'],c['fp']);groups.setdefault(key,[]).append(c['ref'])
  rows=[{'references':refs,'value':v,'footprint':fp,'quantity_per_board':len(refs)} for (v,fp),refs in groups.items()];(dst/'BOM.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  text=['# '+tag+' 委托加工说明','','状态：数字样机加工候选；未上电验证。',f'每台人偶净数量 {quantity} 块；{layers} 层，FR4 成品板厚 {thickness} mm。常规阻焊，建议无铅表面处理。','请按随附 Gerber、独立 PTH/NPTH 钻孔、BOM 与双面贴装坐标核价；元件朝向由原理图/PCB共同确认，不能只凭坐标的角度字段。','所有电容 X7R；限流电阻88.7k必须1%；其余电阻建议1%。回填具体采购料号及替代清单，禁止替代AS5048A为AS5048B，禁止把TPS2553-1锁断型换成自动重试型。','XIAO 两列排针和模块后焊，模块PCB底面与控制板上表面相距4mm；先检查裸板，再装模块。' if tag=='central_c1' else '12×10mm板，用夹边式打印支架；FFC厚0.20±0.03mm，6P，0.5mm间距。连接器在背面，芯片面对磁铁。','先在限流台式电源下做短路、供电与通信检查，再装电池。未授权工厂写磁编码器OTP。','','## 每块板用料','', '| 位号 | 数量 | 参数/型号 | 封装 |','|---|---:|---|---|']
  for r in rows:text.append('| '+','.join(r['references'])+' | '+str(r['quantity_per_board'])+' | '+r['value']+' | '+r['footprint']+' |')
  (dst/'ORDER_NOTES.zh-CN.md').write_text('\n'.join(text)+'\n',encoding='utf8');reports.append({'board':tag,'erc_violations':ec,'drc_violations':len(dr['violations']),'unconnected':len(dr['unconnected_items']),'source_sha256':inputs,'output_sha256':{str(p.relative_to(dst)):sha(p) for p in dst.rglob('*') if p.is_file()},'physical_tested':False})
  if any(sha(p)!=h for p,h in inputs.items()):raise RuntimeError('Source changed during export')
 save('electronics_export.json',{'boards':reports,'manufacturing_qualification':False});print('ELECTRONICS EXPORTED',len(reports))
if __name__=='__main__':main()
