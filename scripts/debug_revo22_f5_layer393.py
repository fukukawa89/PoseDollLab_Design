import sys,json,zlib,struct,numpy as np,shapely
from pathlib import Path
from search_revo22_f5_orientation268 import O
from optimize_revo22_f5_276 import candidates
from build_revo22_fins import solid
from o22_cross_section_geometry import polygon
from o22_f3_gcode import extract_paths
pid=sys.argv[1]if len(sys.argv)>1 else'P033';labels=[sys.argv[2],sys.argv[2]];N=640;img=np.full((N,N*2,3),248,dtype=np.uint8)
def fill(mask,color,alpha=1):
 global panel
 panel[mask]=(panel[mask]*(1-alpha)+np.array(color)*alpha).astype('uint8')
for idx,label in enumerate(labels):
 a=O/'candidates'/pid/label;d=json.loads((a/'verification/native_final.json').read_text());q=(d['external_islands']+d['critical_external_runs'])[0];it=json.loads((a/'verification/plate_manifest.json').read_text())['items'][0];M=np.array(it['rotation_matrix']);t=np.array(it['translation_mm']);bb=q['bounds_mm'];z=q['z_mm'];target=(np.array([(bb[0]+bb[2])/2,(bb[1]+bb[3])/2,z])-t)@M;_,raw=extract_paths(next((a/'projects').glob('*.3mf')),arc_tolerance_mm=.025,max_arc_segment_mm=1);r=np.array(raw).reshape(-1,9);r=r[r[:,7]==0];zs=np.unique(r[:,5]);prev=zs[zs<z-.01][-1];n=np.load(a/'parts'/f'{pid}.npz');xs=np.linspace(target[0]-3,target[0]+3,N);ys=np.linspace(target[1]+3,target[1]-3,N);xx,yy=np.meshgrid(xs,ys);panel=img[:,idx*N:(idx+1)*N,:]
 for vk,fk,col in [('v','f',[133,191,215]),('fin_v','fin_f',[235,136,73]),('teeth_v','teeth_f',[247,214,66])]:
  g=polygon(solid(n[vk],n[fk]).slice(float(prev-(z-prev)/2)));fill(shapely.contains_xy(g,xx,yy),col)
 for lev,col,alpha in[(prev,[50,60,65],.6),(z,[195,20,45],.32)]:
  pp=r[abs(r[:,5]-lev)<.002];aa=(pp[:,:3]-t)@M;bb0=(pp[:,3:6]-t)@M;near=(np.linalg.norm(aa[:,:2]-target[:2],axis=1)<5)|(np.linalg.norm(bb0[:,:2]-target[:2],axis=1)<5);lines=shapely.linestrings(np.stack([aa[near,:2],bb0[near,:2]],1));area=shapely.union_all(shapely.buffer(lines,pp[near,8]/2,quad_segs=8));fill(shapely.contains_xy(area,xx,yy),col,alpha)
 for k in range(0,N,N//6):panel[k,:,:]=[210,215,218];panel[:,k,:]=[210,215,218]
 panel[N//2-2:N//2+3,N//2-14:N//2+15]=[0,0,0];panel[N//2-14:N//2+15,N//2-2:N//2+3]=[0,0,0]
 print('SLICE310',idx,label,'center',target.tolist(),'z',z,'prior',prev,'flag',q,flush=True)
def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
raw=b''.join(b'\x00'+row.tobytes()for row in img);dest=O/f'{pid}_slice393.png';dest.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',N*2,N,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''));print(dest,flush=True)
