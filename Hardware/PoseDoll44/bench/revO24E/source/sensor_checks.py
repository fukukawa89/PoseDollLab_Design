from verify import *
def main(production=False):
    parts=read_saved();by={p['name']:p for p in parts};rows=[]
    actual=production_groups() if production else None
    for r in load(OUT/'profiles/sensor_entries.json')['rows']:
        if r['status']!='DESIGNED_ENTRY':rows.append(r);continue
        p=by[r['board']];s=p['s'];fr=p['frame']
        if r['tail']:
            t=by[r['tail']];s+=moved(t['s'],np.linalg.inv(F0[fr])@F0[t['frame']])
        obstacle=moved(actual[fr],np.linalg.inv(F0[fr])) if actual is not None else union(q['s'] for q in parts if q['frame']==fr and q['role'] in ['structure','rotor','shell']);a=np.array(r['entry_local']);hits=[]
        for d in np.arange(0,30.001,.25):
            vol=(s.translate(a*d)^obstacle).volume()
            if vol>.02:hits.append(dict(travel_mm=float(d),volume_mm3=float(vol)))
        rows.append(dict(**r,verified_status='PASS_GEOMETRY' if not hits else 'FAIL',samples=121,first_block=hits[0] if hits else None,max_overlap_mm3=max([x['volume_mm3'] for x in hits] or [0])))
    wrists=[]
    for side in ['l','r']:
        w=next(w for w in load(OUT/'profiles/wrists.json') if w['side']==side);fr=side+'_wrist_deviation';Q=np.linalg.inv(F0[fr])@F0[side+'_wrist_flex']@np.array(w['mirror']);a=Q[:3,:3]@np.array([0,1,0]);p=by[side+'_E_wrist_magnet'];body=union(q['s'] for q in parts if q['frame']==fr and q['role'] in ['structure','rotor','shell']);s=p['s'];hits=[]
        for d in np.arange(0,15.001,.25):
            vol=(s.translate(a*d)^body).volume()
            if vol>.02:hits.append([float(d),float(vol)])
        keeper=by[side+'_E_magnet_keeper_washer']['s'];stop=None
        for d in np.arange(.1,5,.1):
            if (s.translate(a*d)^keeper).volume()>.02:stop=float(d);break
        wrists.append(dict(side=side,magnet_entry_without_keeper=not hits,first_block=hits[0] if hits else None,positive_keeper_stop_mm=stop,status='PASS_GEOMETRY' if not hits and stop is not None else 'FAIL'))
    put(OUT/('verification/production_sensor_assembly.json' if production else 'verification/sensor_assembly.json'),dict(geometry_sha256=sha(OUT/'assembly_meshes.npz'),production_mesh_sha256=sha(OUT/'production_meshes.npz') if production else None,rows=rows,wrists=wrists,status='PASS_GEOMETRY' if all(r.get('verified_status')=='PASS_GEOMETRY' for r in rows) and all(w['status']=='PASS_GEOMETRY' for w in wrists) else 'FAIL',scope='Board+potted-tail straight paths against integral support; production mode includes fixed descendant frames of each complete production body. Wrist magnets enter open cups before keeper washers. Soldering, IC envelope tolerances and cured adhesive quality remain incoming/physical checks.'))
    print('SENSOR PATHS',[(r['board'],r.get('verified_status',r['status'])) for r in rows],wrists,flush=True)
if __name__=='__main__':main('--production' in sys.argv)
