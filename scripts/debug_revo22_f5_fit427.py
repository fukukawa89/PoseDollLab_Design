from pathlib import Path
p=Path(__file__).parent/'verify_revo22_f5_contacts298.py'
s=p.read_text(encoding='utf-8-sig')
a="    moved=p.transform(relative[:3,:]);env=envelope(moved,rm);changed=float(abs((rm^env).volume()));local_other=moved^windows if changed>VTOL else None;bi=float(max(0.,(before_local^local_other).volume()))if changed>VTOL else None;ai=float(max(0.,(after_local^local_other).volume()))if changed>VTOL else None;relative_cache[ck]=(changed,bi,ai)"
b="""    print('FIT426_BEGIN',pid,name,k,flush=True)
    moved=p.transform(relative[:3,:])
    env=envelope(moved,rm)
    print('FIT426_ENV',float(env.volume()),flush=True)
    changed=float(abs(env.volume()))
    local_other=(moved^windows).as_original() if changed>VTOL else None
    print('FIT426_LOCAL',changed,flush=True)
    bi=float(max(0.,(before_local^local_other).volume()))if changed>VTOL else None
    ai=float(max(0.,(after_local^local_other).volume()))if changed>VTOL else None
    relative_cache[ck]=(changed,bi,ai)"""
assert a in s
p.write_text(s.replace(a,b),encoding='utf-8')
