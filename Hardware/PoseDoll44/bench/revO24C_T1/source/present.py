"""Offline WebGL inspection, printable scale labels and plate maps."""
from kit import *
import base64,shutil,html

def main():
    data=json.loads((OUT/'assembly.json').read_text('utf8'));z=np.load(OUT/'assembly_meshes.npz');rows=[];buf=[];offset=0
    colors={'structure':[.43,.70,.65],'rotor':[.93,.63,.25],'metal':[.58,.64,.71],'bearing':[.18,.25,.30],'friction':[.58,.32,.16],'magnet':[.81,.25,.30]}
    for p in data['parts']:
        i=p['index'];v=z['v'+str(i)];f=z['f'+str(i)];xyz=v[f];n=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
        a=np.concatenate([xyz,np.repeat(n[:,None,:],3,axis=1)],axis=2).reshape(-1,6).astype('<f4');buf.append(a)
        rows.append(dict(p,start=offset,count=len(a),color=colors[p['role']]));offset+=len(a)
    preview=OUT/'preview';preview.mkdir(exist_ok=True)
    (preview/'data.js').write_text('window.KIT='+json.dumps(dict(revision=data['revision'],geometry_sha256=sha(OUT/'assembly_meshes.npz'),parts=rows,locations=data['station_locations'],geometry=base64.b64encode(np.concatenate(buf).tobytes()).decode()),ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    for name in ['index.html','viewer.js','style.css']:shutil.copyfile(HERE/name,preview/name)
    # 1:1 A4 page; the ring has its own engraved 5-degree ticks. The paper adds
    # numbers, so an elephant-foot edge is not used as a dimension reference.
    shapes=['<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297"><rect width="210" height="297" fill="white"/>',
            '<g fill="#172e2c" font-family="Arial" font-size="4"><text x="15" y="15">O24C-T1 / 100% scale / A4</text><text x="15" y="22">Verify the 50 mm line before cutting.</text></g>']
    for st,cy,sgn in [('H',75,-1),('R',175,1)]:
        cx=60;shapes.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="none" stroke="#172e2c" stroke-width=".25"/><circle cx="{cx}" cy="{cy}" r="27" fill="none" stroke="#172e2c" stroke-width=".25"/>')
        # Look from negative Y; screen right is +X, screen down is -Z.
        for q in range(-180,180,5):
            angle=math.radians(sgn*q);x=-math.sin(angle);y=math.cos(angle);r=35 if q%15==0 else 37
            shapes.append(f'<path d="M{cx+x*r:.3f},{cy+y*r:.3f} L{cx+x*40:.3f},{cy+y*40:.3f}" stroke="#172e2c" stroke-width=".22"/>')
            if q%30==0:shapes.append(f'<text x="{cx+x*31.5:.3f}" y="{cy+y*31.5+1:.3f}" text-anchor="middle" font-family="Arial" font-size="2.8">{q}</text>')
        shapes.append(f'<text x="110" y="{cy}" font-family="Arial" font-size="4">{st} / view from -Y</text>')
    shapes.append('<path d="M20,250 h50 m-50,-2 v4 m50,-4 v4" stroke="black" stroke-width=".3"/><text x="28" y="258" font-family="Arial" font-size="4">50 mm</text></svg>')
    (OUT/'printing/scale_labels_A4.svg').write_text(''.join(shapes),encoding='utf8')
    plates=json.loads((OUT/'printing/plates.json').read_text())['plates']
    for plate in plates:
        s=['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="760" viewBox="0 0 180 190"><rect width="180" height="190" fill="#f3f5f1"/><rect x="1" y="1" width="178" height="178" fill="none" stroke="#abc0b9" stroke-width=".3"/>']
        for item in plate['items']:
            m=trimesh.load(OUT/item['stl'],process=True);v=m.vertices;xy=v[:,:2]+item['offset_mm'][:2]
            # actual projected triangles, not a misleading placeholder bounding box
            for tri in m.faces:s.append('<path d="M'+' L'.join(','.join(f'{n:.2f}' for n in xy[j]) for j in tri)+'Z" fill="#8dbbb0" stroke="none"/>')
            lo=xy.min(0);hi=xy.max(0)
            s.append(f'<text x="{(lo[0]+hi[0])/2:.2f}" y="{hi[1]+3:.2f}" font-size="2.6" text-anchor="middle" font-family="Arial" fill="#163c35">{item["id"]}</text>')
        s.append(f'<text x="5" y="187" font-family="Arial" font-size="4">{plate["id"]} / A1 mini 180 x 180 mm</text></svg>')
        (OUT/'printing'/(plate['id']+'.svg')).write_text(''.join(s),encoding='utf8')
    print('PREVIEW',len(rows),'parts',flush=True)

if __name__=='__main__':main()
