import sys,json,math,numpy as np
from build_revo22_fins_v2 import *
from shapely.geometry import box as sb
for pid in sys.argv[1:]:
 n=dict(np.load(O/'parts'/f'{pid}.npz'));r=json.loads((O/'design'/f'{pid}.json').read_text());s=solid(n['v'],n['f']);b=solid(n['fin_v'],n['fin_f']);t=solid(n['teeth_v'],n['teeth_f']);vols=next((x['volumes'] for x in json.loads((D/'all_protected_volumes.json').read_text())['objects'] if x['part']==r['part']),[]);M=np.array(r['orientation']['matrix']);off=np.array(r['orientation']['source_translation_mm']);ban=protected(vols).transform(np.c_[M,off]);done=[]
 for seg in r['segments']:
  if seg['height_mm']<=35 or seg['brace_count'] or seg['blade_thickness_mm']>=seg['height_mm']/12:continue
  bb=seg['bounds_mm'];h=seg['height_mm'];win=sb(bb[0],bb[1],bb[3],bb[4]);poly=polygon(b.slice(h/2)).intersection(win);coords=np.array(poly.minimum_rotated_rectangle.exterior.coords)[:4];edges=np.roll(coords,-1,axis=0)-coords;long=edges[np.argmax(np.linalg.norm(edges,axis=1))];long/=np.linalg.norm(long);cross=np.array([-long[1],long[0]]);base=np.array(poly.centroid.coords[0]);count=0;braces=[]
  # A flange perpendicular to the thin axis, attached well above the bed.
  for bh in [h-2,h-8,h-16]:
   if count:break
   for along in [0,-5,5,-10,10]:
    for across in [0,-1.5,1.5,-3,3]:
     center=base+long*along+cross*across;rot=np.array([[cross[0],-cross[1],0],[cross[1],cross[0],0],[0,0,1.]])
     brace=box([-4,-.9,0],[4,.9,bh]).transform(np.c_[rot,[*center,0]])
     if (brace^s).volume()>1e-8 or (brace^ban).volume()>1e-8 or float(brace.min_gap(s,.3))<.235:continue
     if any((brace.slice(z)^b.slice(z)).area()<.3 for z in [.1,bh/2,bh-.1]):continue
     new=b+brace
     if str(new.status())!='Error.NoError':continue
     b=new;count+=1;braces.append({'bounds_mm':list(brace.bounding_box()),'height_mm':bh,'span_mm':8,'thickness_mm':1.8})
     if count>=2:break
    if count>=2:break
  seg['brace_count']+=count;seg['added_cross_flanges']=braces;done.append((seg['number'],count))
 assert str(b.status())=='Error.NoError' and (b^s).volume()<1e-6
 n.update(fin_v=vf(b)[0],fin_f=vf(b)[1]);np.savez_compressed(O/'parts'/f'{pid}.npz',**n);r.update(support_volume_mm3=float((b+t).volume()),min_gap_mm=min(float(b.min_gap(s,.5)),r['min_gap_mm']));(O/'design'/f'{pid}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('BRACED',pid,done,flush=True)