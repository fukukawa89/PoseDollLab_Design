from revo3_evidence import *

def main():
    v,o=run_paths();root='../../../../verification/revO3/runs/'+os.environ['REVO3_RUN_ID']+'/'
    mapping={'joint':'joint','assembly':'assembly','lifecycle':'lifecycle','electronics':'electronics','pcba_geometry':'pcba_geometry','mass_properties_revO3':'mass_mechanics','mechanics_analysis':'mass_mechanics','status':'status'};data={};receipts=[]
    for name,producer in mapping.items():
        r=ArtifactReader(producer);data[name]=r.json(v/(name+'.json'));receipts.append(r.receipt())
    pr=ArtifactReader('packaging');pr.json(o/'packaging_scene.json');receipts.append(pr.receipt())
    data['reportRoot']=root
    labels={'joint':'关节实体与逐件质量','assembly':'装配 DAG 与名义路径','lifecycle':'独立磨损 / 压缩检查与约束图','electronics':'五种原生板 ERC / DRC','pcba_geometry':'实际 PCBA、目录配合和功能区域','packaging':'两角色包络筛查与未完成项','mass_properties_revO3':'质量移交明细与 41 轴手托载荷','mechanics_analysis':'完整扭矩链与接触反例','firmware_builds':'七角色构建','offline':'兼容与回归测试','baseline':'91 cm 备用与 O2 归档完整性'}
    data['links']=[{'label':label,'href':root+name+'.json'} for name,label in labels.items()]
    text=(HW/'cad/revO3/review.template.html').read_text(encoding='utf-8');html=text.replace('__RUN__',json.dumps(os.environ['REVO3_RUN_ID'])).replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/'))
    (o/'review.html').write_text(html,encoding='utf-8');save(v/'viewer_inputs.json',{'consumed_inputs':receipts})
    print('Viewer generated entirely from sealed current-run reports',flush=True)
if __name__=='__main__':main()
