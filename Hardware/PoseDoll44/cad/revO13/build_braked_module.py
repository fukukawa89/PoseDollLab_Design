from solid_ops import *
from build_finite_twist import housing,rotor_stub,D

def main():
 source=OUT/'printed_core/parts.npz';base=json.loads((OUT/'printed_core/build.json').read_text());extra=base['extensions_mm'];shapes={k:from_tri(t) for k,t in np.load(source).items()}
 for k in ('C01','C02'):
  e=extra[k];plane=18.6+e;stub=rotor_stub().translate([0,0,-e])
  shapes[k]=(shapes[k]^box([-50,-50,-plane if k=='C01' else -50],[50,50,50 if k=='C01' else plane]))+(stub if k=='C01' else pose(stub,D))
 dest=OUT/'braked_module';dest.mkdir(exist_ok=True);records=[]
 for c in json.loads((G9/'bounded_mapping.json').read_text())['characters']:
  key=c['character']+'_'+c['side'];zero=c['paths'][0]['zero_offsets_deg'];lo,hi=(-170,50) if c['side']=='l' else (-55,170)
  pp={k:s.translate([0,0,-extra['C01']]) for k,s in housing(lo+zero[0],hi+zero[0]).items()};dd={k:s.translate([0,0,-extra['C02']]) for k,s in housing(-95+zero[3],105+zero[3]).items()}
  parts={**shapes,**{'P_'+k:s for k,s in pp.items()},**{'D_'+k:s for k,s in dd.items()}};np.savez_compressed(dest/(key+'.npz'),**{k:tri(s) for k,s in parts.items()});records.append({'id':key,'parts':{k:record(s) for k,s in parts.items()}})
 save('braked_module/build.json',{'source_sha256':sha(source),'extension_mm':extra,'characters':records,'scope':'Printed core with inherited outer twist envelope concepts. Full outer twist preload/wiring design still pending.','manufacturing_released':False});print('built',len(records))
if __name__=='__main__':main()
