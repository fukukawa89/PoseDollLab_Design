"""Full O22 print batch, native geometry round trip, and actual hardware counts."""
from pathlib import Path
import copy,json,shutil,collections,sys,numpy as np
import build_revo22_assembly as a
b=a.b;g=a.g;B=a.B;H=a.H;D=a.D
from export_print_batch import orient
import print_io17,print_io20

def main():
 p,m,raw,changed,service,C=a.model();old=g.read(H/'bench/revO20/print_batch/manifest.json');folder=B/'print_batch';folder.mkdir(exist_ok=True);rows=[];ids={};gone=set(g.read(D/'assembly_metadata.json')['removed_parts'])|set(changed)
 for original in old['rows']:
  row=copy.deepcopy(original);row['instances']=[i for i in row['instances'] if i['part'] not in gone]
  if not row['instances']:continue
  row['quantity_by_character']={'universal':len(row['instances'])};rows.append(row)
  for i in row['instances']:ids[i['part']]=row['id']
  for ext in ['stl','3mf']:shutil.copy2(H/'bench/revO20/print_batch'/(row['id']+'.'+ext),folder/(row['id']+'.'+ext))
 for index,(key,shape) in enumerate(changed.items(),1):
  A=np.array(m[key]['transform']);A[:3,1]*=1 if np.linalg.det(A[:3,:3])>0 else -1
  s=g.move(shape,np.linalg.inv(A)).simplify(1e-10);bedshape,bed=orient(s);assert g.solid_count(bedshape)==1,(key,g.solid_count(bedshape))
  pid=f'X{index:03}';fmt=print_io20.stl(folder/(pid+'.stl'),bedshape);print_io17.write_3mf(folder/(pid+'.3mf'),{pid:bedshape});ids[key]=pid
  rows.append({'id':pid,'instances':[{'character':'universal','part':key,'body':m[key]['body'],'print_id':pid}],'quantity_by_character':{'universal':1},'stl':'print_batch/'+pid+'.stl','stl_sha256':g.sha(folder/(pid+'.stl')),'bed':bed,'stl_format':fmt,'geometry_source':'O22 actual assembled solid; proper rotation to manufacturing coordinates','physical_tested':False,'material_note':'Retain proven O11 material/process. Re-slice; CAD support diagnostic is not a print-process qualification.'})
  print('PRINT',pid,key,fmt,flush=True)
 printed={k for k in p if not m[k].get('sku')};fixture={i['part'] for r in rows for i in r['instances'] if i['part'] not in printed}
 assert set(ids)==printed|fixture,(sorted(printed-set(ids)), sorted(set(ids)-printed-fixture))
 count=sum(len(r['instances']) for r in rows);volume=sum(float(p[k].volume()) for k in printed)
 b.put(folder/'manifest.json',{'schema':'POSEDOLL-O22-PRINT/1','status':'ENGINEERING_FIRST_ARTICLE','units':'mm','rows':rows,'print_types':len(rows),'print_pieces':count,'on_doll_print_pieces':len(printed),'assembly_fixture_pieces':len(fixture),'physical_tested':False,'o11_coupon_user_test':'PASS_REPORTED_2026-09-30','o11_friction_geometry_changed':False,'source_snapshot':'O21 5537190 + O20 900f572 + O22 sources'})
 oldp,oldm,_=b.baseline();oldvol=sum(float(v.volume()) for k,v in oldp.items() if not oldm[k].get('sku'))
 b.put(D/'material_comparison.json',{'O20_on_doll_prints':sum(not x.get('sku') for x in oldm.values()),'O22_on_doll_prints':len(printed),'O20_printed_solid_volume_mm3':oldvol,'O22_printed_solid_volume_mm3':volume,'delta_solid_volume_mm3':volume-oldvol,'solid_material_equivalent_delta_g_at_1_24':(volume-oldvol)*.00124,'slicer_mass_measured':False,'whole_device_mass_measured':False,'reason':'Larger routed backboard enclosure; count electronics assemblies, not visualization envelopes.'})
 counts=collections.Counter(mm.get('sku') for mm in m.values() if mm.get('sku'))
 proc=g.read(H/'bench/revO20/procurement.json');pr=[]
 for r in proc['characters'][0]['rows']:
  if r['category']!='金属/磁铁标准件':continue
  qty=counts.get(r['sku'],0)
  if not qty:continue
  r=copy.deepcopy(r);r['net_quantity']=qty;r['optional_spares']=int(np.ceil(.1*qty));r['suggested_total']=qty+r['optional_spares'];pr.append(r)
 pr.append({'sku':'SELF_TAP_M2_L6','name_zh':'塑料自攻 M2×6，头径≤4mm；新中央板安装','category':'金属/磁铁标准件','net_quantity':4,'optional_spares':2,'suggested_total':6})
 for sku,name,qty,sp in [('MT6701_PCBA','O22 五线传感板，工厂焊接并标号',46,2),('O22_4L_CARRIER','O22 四层中央采集板，80×94mm',1,0),('XIAO_ESP32S3','XIAO ESP32S3 普通版',1,0),('CABLE_TIE_2P5','2.5mm 扎带（含双重尾线固定、躯干分束与盖板）',65,10)]:pr.append({'sku':sku,'name_zh':name,'category':'电子/线束','net_quantity':qty,'optional_spares':sp,'suggested_total':qty+sp})
 b.put(B/'procurement.json',{'status':'O22_COUNTS_FROM_CAD_MOQ_PENDING','characters':[{'character':'universal','rows':pr}],'electronic_detail':'manufacturing/electronic_bom.json','avoid_double_billing':'PCBA and harness allocations have separate scopes; envelopes are not extra purchased components.'})
 b.put(D/'print_ids.json',ids);print('PRINT COMPLETE',len(rows),count,volume,flush=True)
if __name__=='__main__':main()
