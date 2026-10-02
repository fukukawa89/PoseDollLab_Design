"""Fit complete finite twist modules to the face-brake core; baseline kept separate."""
from solid_ops import *
from build_finite_twist import housing,rotor_stub,D

def main():
 source=OUT/'face_brake/parts.npz';base=json.loads((OUT/'face_brake/build.json').read_text());extra=base['extra_fork_extension_each_mm'];shapes={k:from_tri(t) for k,t in dict(np.load(source)).items()};stub=rotor_stub().translate([0,0,-extra]);plane=18.6+extra
 shapes['C01']=(shapes['C01']^box([-40,-40,-plane],[40,40,40]))+stub
 shapes['C02']=(shapes['C02']^box([-40,-40,-40],[40,40,plane]))+pose(stub,D)
 dest=OUT/'braked_module';dest.mkdir(exist_ok=True);records=[]
 for c in json.loads((G9/'bounded_mapping.json').read_text())['characters']:
  key=c['character']+'_'+c['side'];zero=c['paths'][0]['zero_offsets_deg'];lo,hi=(-170,50) if c['side']=='l' else (-55,170)
  pp={k:s.translate([0,0,-extra]) for k,s in housing(lo+zero[0],hi+zero[0]).items()};dd={k:s.translate([0,0,-extra]) for k,s in housing(-95+zero[3],105+zero[3]).items()}
  parts={**shapes,**{'P_'+k:s for k,s in pp.items()},**{'D_'+k:s for k,s in dd.items()}};np.savez_compressed(dest/(key+'.npz'),**{k:tri(s) for k,s in parts.items()});records.append({'id':key,'parts':{k:record(s) for k,s in parts.items()}})
 save('braked_module/build.json',{'source_sha256':sha(source),'extra_extension_mm':extra,'characters':records,'scope':'Face brake core plus previous finite twist housing concept. Outer twist holding/preload and complete harness remain unqualified.','manufacturing_released':False});print('built',len(records),flush=True)
if __name__=='__main__':main()
