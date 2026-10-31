"""Import routed sensor variants and run native ERC, DRC and schematic parity."""
from electronics_carrier import *

def main():
    folder=OUT/'electronics/sensors';manifest=json.loads((folder/'manifest.json').read_text('utf8'))
    for row in manifest['variants']:
        dest=folder/row['variant'];name=row['name'];fn=dest/(name+'.kicad_pcb')
        pro=json.loads((dest/(name+'.kicad_pro')).read_text('utf8'))
        b=p.LoadBoard(str(dest/'route_input.kicad_pcb'));assert p.ImportSpecctraSES(b,str(dest/'route.ses'))
        for q in b.GetTracks():
            if isinstance(q,p.PCB_VIA):q.SetWidth(p.FromMM(.4));q.SetDrill(p.FromMM(.2))
            elif q.GetWidth()<p.FromMM(.12):q.SetWidth(p.FromMM(.12))
        b.BuildConnectivity();p.SaveBoard(str(fn),b);put(dest/(name+'.kicad_pro'),pro)
        result={}
        for typ,args,ext in [('erc',['sch','erc'],'.kicad_sch'),('drc',['pcb','drc'],'.kicad_pcb')]:
            subprocess.run([str(CLI),*args,'--format','json','--severity-all','-o',str(dest/(typ+'.json')),str(dest/(name+ext))],capture_output=True,check=True)
            a=json.loads((dest/(typ+'.json')).read_text('utf8'));vv=a.get('violations',[])+[v for sh in a.get('sheets',[]) for v in sh.get('violations',[])]
            result[typ]=dict(violations=len(vv),unconnected=len(a.get('unconnected_items',[])),parity=len(a.get('schematic_parity',[])))
        row.update(checks=result,routing_complete=not any(any(c.values()) for c in result.values()),pcb_sha256=hashlib.sha256(fn.read_bytes()).hexdigest());print(row['variant'],result,flush=True)
    put(folder/'manifest.json',manifest)
if __name__=='__main__':main()
