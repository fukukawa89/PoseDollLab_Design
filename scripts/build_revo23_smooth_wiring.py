"""Reattach real wire seats without cutting notches into new round members."""
from revo23_smooth import *
from verify_revo23_g import rod_body,wall_pad
import build_revo23_wire_seats as seats
import build_revo23_clean_wiring as previous

def setup():
    parts,p,cfg=load_g();N=frames(p,p['neutral_raw_deg']);kept={}
    shutil.copytree(FHISTORY/'profiles',GROOT/'profiles',dirs_exist_ok=True)
    for key,item in parts.items():
        if item['role']!='structure':continue
        keep=raw_keep(key,parts,p,N);path=GROOT/(key.replace('/','__')+'.json')
        if path.exists():
            rods=read(path)['rods']
            keep+=move(union([rod_body(r) for r in rods]+[wall_pad(r) for r in rods if 'target_mount' not in r]),np.linalg.inv(N[item['token']]))
        kept[key+'|v'],kept[key+'|f']=vf(keep)
    (GROOT/'source').mkdir(exist_ok=True);np.savez_compressed(GROOT/'source/retained_interfaces.npz',**kept)
    case=GROOT/'o22__controller_housing.npz'
    if not case.exists():save_s(case,parts['o22/controller_housing']['s'])
    if not (GROOT/'wire_seats.json').exists():
        old=read(FHISTORY/'harness/wire_seats.json');old['seats']=[r for r in old['seats'] if r['part']=='o22/controller_housing'];put(GROOT/'wire_seats.json',old)
    return parts,p,cfg

def configure(m):
    m.load_e=load_g;m.EROOT=GROOT;m.DHISTORY=GROOT;m.DHASH=FHASH
    m.local_skin=lambda key,p,cfg:skin_of(key)

def positions(body,N,cfg,needed,host=None):
    geom=canonical(body,N,cfg);outer=move(geom[1],np.linalg.inv(N)@geom[3]) if geom else None
    for r in read(FHISTORY/'harness/wire_seats.json')['seats']:
        if r['body']==body and r['part'].startswith('frame/'):
            yield np.array(r['transform_body_mm']),outer,dict(previous_seat=r['id'])
    yield from previous.positions(body,N,cfg,needed,host)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--keys',nargs='*');ap.add_argument('--mode',choices=['seats','channels','route','verify'],default='seats');a=ap.parse_args()
    setup();configure(seats);seats.candidate_positions=positions
    if a.mode=='seats':seats.build_seats(a.keys)
    elif a.mode=='channels':
        import channel_revo23_harness as channels
        configure(channels);channels.main(a.keys)
    elif a.mode=='route':
        import route_revo23_harness as route
        configure(route);route.main()
    else:import verify_revo23_wire_fixtures
