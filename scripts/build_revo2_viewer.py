from revo2_evidence import *

def main():
 verify,out=run_paths();root='../../../../verification/revO2/runs/'+os.environ['REVO2_RUN_ID']+'/'
 data={name:read(verify/(name+'.json')) for name in ['joint','assembly','electronics','mass_properties_revO2','mechanics_analysis','status']};data['reportRoot']=root
 labels={'joint':'关节实体与逐件质量','assembly':'装配、后盖、工具和旋转路径','electronics':'原生 ERC / DRC 完整结果','pcba_geometry':'实际模型覆盖与配合头缺口','packaging':'两角色空间失败记录','mass_properties_revO2':'全部质量、质心和 41 轴载荷','mechanics_analysis':'承力、公差与键空程预算','power_budget':'五伏电源、分支与线束分配','firmware_builds':'七角色构建与配置身份','offline':'兼容与反例测试','baseline':'91 cm 备用哈希完整性'}
 data['links']=[{'label':label,'href':root+name+'.json'} for name,label in labels.items() if (verify/(name+'.json')).is_file()]
 template=(HW/'cad/revO2/review.template.html').read_text(encoding='utf-8');html=template.replace('__RUN__',json.dumps(os.environ['REVO2_RUN_ID'])).replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/'))
 (out/'review.html').write_text(html,encoding='utf-8');print('Viewer generated from current-run evidence')
if __name__=='__main__':main()