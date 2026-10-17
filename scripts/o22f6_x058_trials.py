from pathlib import Path
import sys,json,zipfile,xml.etree.ElementTree as ET,concurrent.futures
import numpy as np
from o22f6_holeclear import WORK,SRC,R,put
from prepare_revo22_f3 import slicer

def trial(spec):
 label,changes=spec;folder=WORK/f'process_trials/X058/{label}';folder.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(WORK/'build/D01/input.3mf')as z:data={k:z.read(k)for k in z.namelist()}
 root=ET.fromstring(data['Metadata/model_settings.config'])
 for obj in root.findall('object'):
  if not any('X058'in q.get('value','')for q in obj.findall('metadata')):continue
  for k,v in changes.items():
   q=next((x for x in obj.findall('metadata')if x.get('key')==k),None)
   if q is None:q=ET.SubElement(obj,'metadata',{'key':k})
   q.set('value',v)
 data['Metadata/model_settings.config']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
 source=folder/'input.3mf';dest=folder/'trial.3mf'
 with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED)as z:
  for k,v in data.items():z.writestr(k,v)
 report=slicer(source,dest,folder/'slice',timeout=600);assert report['complete'],report
 import verify_revo22_f4_local_extrusion as check
 extract=check.extract_detailed
 def narrowed(*args,**kwargs):
  rep,raw,features,names=extract(*args,**kwargs);a=np.asarray(raw).reshape(-1,9);features=np.array(features);mask=(a[:,5]>47.8)&(a[:,5]<50.6)&(a[:,0]>3)&(a[:,0]<89)&(a[:,1]>71)&(a[:,1]<174)
  return rep,a[mask],features[mask],names
 check.extract_detailed=narrowed;r=check.check(dest,folder/'local_hole_layers.json');check.extract_detailed=extract
 result=dict(label=label,changes=changes,islands=r['detached_bead_regions'],unresolved_count=r['unresolved_count'],max_span_mm=r['max_unresolved_span_mm'],project_sha256=r['project_sha256']);put(folder/'result.json',result);print('PROCESS_TRIAL',label,len(result['islands']),result['unresolved_count'],flush=True);return result

if __name__=='__main__':
 specs=[('angle45',{'bridge_angle':'45'}),('angle90',{'bridge_angle':'90'}),('angle135',{'bridge_angle':'135'}),('walls_first',{'is_infill_first':'0'}),('walls_first90',{'is_infill_first':'0','bridge_angle':'90'}),('outer_first',{'is_infill_first':'0','wall_sequence':'outer wall/inner wall'})]
 with concurrent.futures.ProcessPoolExecutor(max_workers=2)as pool:
  for x in pool.map(trial,specs):pass
