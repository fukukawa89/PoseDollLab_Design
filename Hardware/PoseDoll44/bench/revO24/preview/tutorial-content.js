'use strict';
window.O24_LESSONS = (() => {
  const motions = {
    clavicle_protract:{short:'肩带前后',parent:'chest',child:'collar_z',axis:[0,0,-1],keys:[0,15,0,-15,0],fixed:'胸部安装座',moving:'两轴锁骨组件与整条手臂',text:'竖直轴穿过锁骨根部 C。胸部支座不动，锁骨和整条手臂围绕这根轴前后摆。'},
    clavicle_elevate:{short:'抬肩 / 下压',parent:'collar_z',child:'collar',axis:[1,0,0],keys:[0,20,0,-8,0],fixed:'锁骨前后摆动的输出架',moving:'锁骨连架与整条手臂',text:'第二根轴同样经过 C。它横向穿过支座，让锁骨连架抬高或下压，肩中心随之移动。'},
    shoulder_flex:{short:'前举 / 后伸',parent:'shoulder_base',child:'shoulder_pitch',axis:[0,-1,0],keys:[0,120,0,-25,0],fixed:'锁骨末端支座',moving:'开口叉架与整条手臂',text:'靠身体一侧的轴承支座留在锁骨上。轴带动开口叉架转动，手臂围绕肩中心 S 向前举或向后伸。'},
    shoulder_abduct:{short:'向侧面抬臂',parent:'shoulder_pitch',child:'shoulder_swing',axis:[1,0,0],keys:[0,80,0,40,0],fixed:'开口叉架',moving:'横向转动头与手臂',text:'开口叉架两端支撑一对短轴。横向转动头绕这根轴转动，把手臂向身体外侧抬起。'},
    upperarm_roll:{short:'上臂内外旋',parent:'shoulder_swing',child:'upper',axis:[0,0,-1],keys:[0,55,0,-55,0],base:{elbow_flex:90},fixed:'上臂环形轴承座',moving:'上臂中轴、肘和前臂',text:'转轴沿肩 S 到肘 E 的骨线。弯肘只是为了看清方向：上臂自转时，弯着的前臂会一起扫过一个圆弧。'},
    elbow_flex:{short:'屈肘 / 伸直',parent:'elbow_base',child:'elbow',axis:[0,-1,0],keys:[0,120,0,60,0],fixed:'上臂末端的左右叉架',moving:'肘转子、前臂和手',text:'左右叉架夹住肘部转子，两侧轴承支撑同一根轴。转子绕肘中心 E 转动，前臂和手一起弯过来。'},
    forearm_roll:{short:'翻掌 / 覆掌',parent:'elbow',child:'fore',axis:[0,0,-1],keys:[0,70,0,-70,0],base:{elbow_flex:90},fixed:'肘部输出架与前臂轴承座',moving:'前臂中轴、腕和手掌',text:'两只轴承围绕肘 E 到腕 W 的直线支撑中空轴。外壳不跟着翻转，轴、腕和手掌一起转；腕中心不会绕骨线画圈。'},
    wrist_flex:{short:'屈腕 / 背伸',parent:'wrist_base',child:'wrist_flex',axis:[0,1,0],keys:[0,50,0,-40,0],base:{elbow_flex:90},fixed:'前臂末端输入叉',moving:'中央十字块、输出叉和手掌',text:'输入叉两侧的短轴让中央十字块摆动。后面的输出叉和手掌一起跟随，形成屈腕或背伸。'},
    wrist_deviation:{short:'尺偏 / 桡偏',parent:'wrist_flex',child:'hand',axis:[1,0,0],keys:[0,25,0,-15,0],base:{elbow_flex:90},fixed:'中央十字块及其第二对短轴',moving:'输出叉、其轴承外圈和手掌',text:'第二对短轴留在十字块上，输出叉通过轴承绕它们摆动。这次运动的是叉架一侧；轴承外圈跟着手掌，内圈应留在短轴上。'}
  };
  const chapters = [
    {id:'elbow',title:'肘：像门轴一样弯曲',nav:'肘关节',sub:'先理解一根转轴',range:[63,80],motions:['elbow_flex'],anchor:'elbow_base',span:150,yaw:.78,pitch:.24,
      intro:'先固定上臂，再看前臂绕哪里转。肘只有一个主要弯曲自由度。',takeaway:'紫色轴线与粉色骨线在 E 点相交。叉架虽然分在两侧，真正的旋转中心仍在骨架上。',limit:'轴承在模型里以单个环形实体表示，内部的内圈、外圈和滚珠未分别建模。',
      labels:[['elbow_fork_14','上臂叉架'],['elbow_bearing_1','轴承'],['elbow_hub','肘转子'],['elbow_magnet','转动磁铁'],['elbow_pcb','固定传感板']]},
    {id:'forearm',title:'前臂：沿骨线翻转',nav:'前臂旋转',sub:'为什么手腕不会偏心',range:[81,93],motions:['forearm_roll'],anchor:'elbow',span:160,yaw:1.05,pitch:.6,
      intro:'弯肘后翻掌、覆掌，观察手腕中心有没有离开前臂的轴线。',takeaway:'转轴沿 E—W 方向。轴承可以布置在骨段中间；轴线经过肘和腕，不要求轴承正好放在肘点上。',limit:'中空轴端的磁铁会挡住中心通路，实际线束需要绕行；转轴与管件的锁固仍待细化。',
      labels:[['forearm_housing','不转的轴承座'],['forearm_bearing_31','两端轴承'],['forearm_shaft','同轴转动轴'],['forearm_magnet','转动磁铁'],['forearm_pcb','固定传感板']]},
    {id:'wrist',title:'手腕：两根轴交在一点',nav:'手腕',sub:'短轴如何互相避让',range:[94,123],motions:['wrist_flex','wrist_deviation'],anchor:'wrist_base',span:105,yaw:.85,pitch:.4,
      intro:'先看上下弯腕，再看左右偏腕。两组运动共享腕中心 W。',takeaway:'两根“轴线”相交，实体使用两对短轴。短轴不会在中心互相穿透，中央十字块负责连接两组运动。',limit:'尺偏 / 桡偏时，轴承外圈随输出叉转动。模型中的单环表示法不能展示轴承内部的相对运动。',
      labels:[['wrist_input_fork_10','前臂输入叉'],['wrist_cross','中央十字块'],['wrist_flex_stub_10','第一对短轴'],['wrist_dev_stub_9','第二对短轴'],['hand_palm','输出叉与手掌']]},
    {id:'shoulder',title:'肩：三种旋转，共同一点',nav:'肩关节',sub:'开口叉架里的三根轴',range:[26,62],motions:['shoulder_flex','shoulder_abduct','upperarm_roll'],anchor:'shoulder_base',span:148,yaw:.95,pitch:.22,
      intro:'依次观察前举、外展和上臂自转。前一级支架转动时，会把后一级一起带走。',takeaway:'三根旋转轴都经过肩中心 S。外侧的开口叉架为手臂让出活动空间，上臂中轴仍沿 S—E 骨线。',limit:'肩外展接近 90° 时，第一轴与第三轴接近重合，存在万向架奇异位形。本教程外展示范到 80°；操作手感仍需实物评估。',
      labels:[['shoulder_pitch_housing','锁骨末端支座'],['shoulder_open_yoke','开口叉架'],['shoulder_cross_head','横向转动头'],['humeral_housing','上臂轴承座'],['humeral_shaft','上臂中轴']]},
    {id:'clavicle',title:'肩带：让肩点一起移动',nav:'锁骨与肩带',sub:'整条手臂的上游支座',range:[0,25],motions:['clavicle_protract','clavicle_elevate'],anchor:'chest',span:123,yaw:.9,pitch:.28,
      intro:'肩膀除了转动，还会随锁骨前后移动、抬高和下压。这里用两根相交轴表达肩带运动。',takeaway:'两个方向的轴承座沿轴线错开布置；两根轴线仍在锁骨根 C 相交。转动肩带时，肩点 S 随连架移动。',limit:'当前只设计左侧接口。另一侧锁骨、完整胸腔和头部的空间关系还没有完成验证。',
      labels:[['chest_mount','胸部安装座'],['clavicle_z_housing','前后摆动支座'],['clavicle_elevation_housing','抬肩支座'],['clavicle_link_1','锁骨连架'],['clavicle_x_pcb','测角传感板']]},
    {id:'whole',title:'整条手臂：从胸部到手掌',nav:'整臂总览',sub:'把所有模块串起来',range:[0,123],motions:Object.keys(motions),anchor:'shoulder_base',span:340,yaw:.95,pitch:.15,
      intro:'拆解模式按模块展开，装配模式从胸部接口向手掌逐段装回。旋转模式可选看任意一根轴。',takeaway:'9 根测角轴 = 肩带 2 + 肩 3 + 肘 1 + 前臂 1 + 腕 2。骨线对齐约束的是中心和轴线，局部叉架可以分布在骨线两边。',limit:'560 mm 是对应 UE 人物的参考身高。完整 O24 人偶尚未制成；这里展示的是左臂数字布局。',
      labels:[['clavicle_link_1','肩带'],['shoulder_open_yoke','肩与上臂'],['elbow_hub','肘'],['forearm_housing','前臂'],['wrist_cross','腕'],['hand_palm','手掌']]}
  ];
  const steps = [
    {title:'放置承力支架',text:'先找到壳体、叉架和支座。它们决定孔位与轴线，也承接来自下一段手臂的力。'},
    {title:'让轴承对准支座孔',text:'轴承负责径向支撑。内外圈分别与轴和支座配合，让两侧可以相对转动；单环模型没有展开轴承内部。'},
    {title:'对齐转轴和转动件',text:'轴、转子和输出结构回到共同轴线上。它们把关节的转动传给下一段；具体定位和锁紧结构还需补齐。'},
    {title:'对齐摩擦片与压紧件',text:'摩擦片位于相对转动的接触面，用预紧产生持姿阻力。压片和轴端件回到名义位置；预紧闭合路径仍待设计验证。'},
    {title:'磁铁放在转动一侧',text:'径向充磁磁铁的方向随转角变化。这里标示安装位置，专用磁铁座和防转锁固还没有完成。'},
    {title:'传感板留在另一侧',text:'传感板隔着空气间隙读取磁场方向。板、支架和插头属于支承一侧；传感器不负责承重，也不负责让关节保持姿势。'}
  ];
  const wholeSteps = [
    {title:'胸部接口与肩带',text:'先建立整条手臂的上游参考，肩带的两根轴线经过锁骨根 C。'},
    {title:'肩关节与上臂',text:'三轴肩组件接到锁骨末端。肩中心 S、上臂中轴和肘中心 E 的位置关系由骨架决定。'},
    {title:'肘关节',text:'肘部左右叉架位于上臂末端，横向转轴经过 E。'},
    {title:'前臂旋转组件',text:'前臂轴承座与肘转子连接，前臂中轴沿 E—W 方向布置。'},
    {title:'两轴手腕',text:'腕部输入叉、十字块和输出叉围绕 W 排布，两组短轴分担两个方向的运动。'},
    {title:'刚性手掌',text:'手掌连接腕部输出叉。完成的是模块关系展示；具体螺钉、定位面和装配工艺仍需制造设计。'}
  ];
  const parent = {chest:null,collar_z:'chest',collar:'collar_z',shoulder_base:'collar',shoulder_pitch:'shoulder_base',shoulder_swing:'shoulder_pitch',upper:'shoulder_swing',elbow_base:'upper',elbow:'elbow_base',fore:'elbow',wrist_base:'fore',wrist_flex:'wrist_base',hand:'wrist_flex'};
  const descendant = (frame, ancestor) => {for(let f=frame;f;f=parent[f])if(f===ancestor)return true;return false};
  function group(p){return p.i<26?0:p.i<63?1:p.i<81?2:p.i<94?3:p.i<123?4:5}
  function stage(p){
    if(/_(pcb|connector|sensor_holder)$/.test(p.name))return 5;
    if(p.role==='magnet')return 4;
    if(p.role==='friction'||/_(pressure_[-\d]+|head|nut)$/.test(p.name))return 3;
    if(p.role==='bearing')return 1;
    if(p.role==='metal'||p.role==='rotor'||/^(upperarm_centered|forearm_centered|wrist_output|wrist_dev_ear|hand_palm)/.test(p.name))return 2;
    return 0;
  }
  const categories=['支架与外壳','轴承','轴与转动件','摩擦与压紧件','磁铁','传感板与支架'];
  const names = {housing:'轴承座',sensor_holder:'传感板支架',pcb:'传感板',connector:'插头占位',magnet:'测角磁铁',bearing:'轴承',shaft:'转轴',stub:'短轴',friction:'摩擦片',brake:'摩擦片',pressure:'压片',flange:'转动法兰',rotor:'转动件',hub:'中央转子',head:'轴端头',nut:'轴端螺母',ear:'轴承支耳',fork:'叉架',stem:'支撑臂',washer:'摩擦垫片',support:'支撑臂',output:'输出块'};
  const exact={chest_mount:'胸部安装座',shoulder_open_yoke:'肩部开口叉架',shoulder_cross_head:'肩部横向转动头',wrist_cross:'腕部中央十字块',hand_palm:'刚性手掌',upperarm_centered_tube:'上臂中心管',forearm_centered_tube:'前臂中心管'};
  function partName(p){if(exact[p.name])return exact[p.name];if(p.name.startsWith('clavicle_link'))return '锁骨连架';let t=Object.keys(names).find(k=>p.name.includes('_'+k));return t?names[t]:categories[stage(p)]}
  return {motions,chapters,steps,wholeSteps,parent,descendant,group,stage,categories,partName};
})();
