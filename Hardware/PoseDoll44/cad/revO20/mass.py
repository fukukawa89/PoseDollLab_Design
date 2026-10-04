"""Material accounting; never present solid CAD density as a weighed doll."""
from base import *
from load_budget import density

def quantities(p,m):
 vol=sum(s.volume() for k,s in p.items() if m[k]['sku'] is None);stock=0.;rows=[]
 for k,s in p.items():
  sku=m[k]['sku']
  if sku is None:continue
  d,note=density(sku);mass=s.volume()*d*1000
  if sku in ('XIAO_ESP32S3','POLOLU_D24V22F3'):mass={'XIAO_ESP32S3':4,'POLOLU_D24V22F3':6}[sku]
  stock+=mass
 return {'modeled_parts':len(p),'on_doll_print_count':sum(m[k]['sku'] is None for k in p),'print_volume_mm3':float(vol),'PLA_CF_solid_equivalent_g':float(vol*.00122),'PETG_solid_equivalent_g':float(vol*.00127),'hardware_electronics_envelope_estimate_g':stock,'PLA_CF_modeled_total_equivalent_g':float(vol*.00122+stock),'PETG_modeled_total_equivalent_g':float(vol*.00127+stock)}

def main():
 p,m,pr,st,prov=load_o19();old=quantities(p,m);changes=g.read(OUT/'changes.json');npz=np.load(OUT/'changed_parts.npz');gone=set(changes['removed_stock_parts'])|{k for r in changes['replacements'] for k in r['replaces']};new={k:s for k,s in p.items() if k not in gone};new.update({k:g.move(from_tri_exact(t),m[k]['transform']) for k,t in npz.items()});now=quantities(new,m)
 rows=[]
 for r in changes['replacements']:
  before=sum(p[k].volume() for k in r['replaces']);after=new[r['part']].volume();rows.append({'part':r['part'],'before_mm3':before,'after_mm3':after,'removed_mm3':before-after,'PLA_CF_solid_equivalent_saved_g':(before-after)*.00122})
 delta={k:old[k]-now[k] for k in old};result={'status':'CAD_ESTIMATE_NOT_WEIGHED','O19':old,'O20':now,'reduction':delta,'printed_material_reduction_percent':100*delta['print_volume_mm3']/old['print_volume_mm3'],'parts':rows,'density_sources':{'PLA_CF_g_cm3':1.22,'PLA_CF_source':'https://store.bblcdn.eu/s8/default/aefa8303ad8d40248b0d86dfdad46518/Bambu_PLA-CF_Technical_Data_Sheet_V3.pdf','PETG_g_cm3':1.27,'PETG_basis':'Inherited O15 budgeting assumption, not a new measured property','steel_g_cm3':7.9,'steel_basis':'Inherited O15 envelope estimate'},'limits':['CAD solid-volume equivalent, not sliced plastic mass. Sparse infill can reduce the apparent saving from internal cores; compare identical slicer settings before printing.','Actual total excludes soft wire/USB tether, adhesive, ties and slicer supports. Electronics use simplified envelopes and provisional masses.','Assembly fixture and optional spare hardware are excluded from worn mass.','No stiffness/creep, measured friction torque or UE capture results are fabricated.']};g.write(OUT/'mass_comparison.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('parts','density_sources','limits')},indent=2),flush=True)
if __name__=='__main__':main()
