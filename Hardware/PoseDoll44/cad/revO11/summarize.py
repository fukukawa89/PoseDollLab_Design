from solid_ops import *
def main():
 def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
 target=read(OUT/'braked_module/target_motion.json');body=read(OUT/'clavicle_trial/motion.json');continuous=read(OUT/'printed_core/continuous_yokes.json');bench=read(H/'bench/revO11/plan.json');loads=read(OUT/'loads.json');assembly=read(OUT/'assembly_and_stack.json')
 assert target['complete'] and body['complete'] and len(target['cases'])==204 and len(body['cases'])==102
 result={'targets':len(target['cases']),'targetFailures':sum(bool(x['findings']) for x in target['cases']),'bodyTargets':len(body['cases']),'bodyFailures':sum(bool(x['findings']) for x in body['cases']),'clearance':continuous['required_mm'],'continuousCells':len(continuous['certified_cells']),'singleSiteTargetNm':bench['single_site_screening_target_Nm'],'moduleSolidMassG':loads['characters'][0]['modeled_module_solid_mass_g'],'physicalTested':False,'manufacturingReleased':False}
 save('summary.json',{'summary':result,'remainingCollisions':[r for r in body['cases'] if r['findings']],'selectedLayout':body['candidate'],'scope':'Scoped nominal geometry and load budget; printing, materials, electronics and complete human-shaped assembly remain unqualified.'})
 (H/'tutorials/print-first/results.js').write_text('window.O11_RESULTS='+json.dumps(result,ensure_ascii=False)+';\n',encoding='utf-8');print(result)
if __name__=='__main__':main()
