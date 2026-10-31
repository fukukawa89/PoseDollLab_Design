'use strict';
// Face tint is a teaching overlay on the existing mesh, not a new CAD surface.
window.HardwareGuide={
 fragmentShader:`precision mediump float;
 uniform vec3 color, faceNormal, facePoint, featureCenter;
 uniform float opacity, featureKind, featureRadius, featureDepth, featureBore;
 varying vec3 normal, localPosition, localNormal;
 void main(){
   vec3 paint=color;
   vec3 q=localPosition-featureCenter;
   float radius=length(q-faceNormal*dot(q,faceNormal));
   float fromFace=dot(localPosition-facePoint,faceNormal);
   float facing=dot(normalize(localNormal),faceNormal);
   if(featureKind>1.5 && featureKind<2.5 && fromFace>-.035 && facing>.7) paint=vec3(.09,.65,.42);
   if(featureKind>.5 && featureKind<1.5 && radius<featureRadius &&
      ((fromFace>-.035 && facing>.7) ||
       (fromFace>-.26*featureDepth && radius<featureBore+.055))) paint=vec3(.10,.39,.94);
   if(featureKind>2.5){paint=vec3(.18,.46,.82);if(radius<featureBore+.3&&fromFace>-.08)paint=vec3(.35,.78,1.);}
   float light=.55+.45*abs(dot(normalize(normal),normalize(vec3(.3,.5,1.))));
   gl_FragColor=vec4(paint*light,opacity);
 }`,
 color:o=>o.kind==='spring'?'#245fd2':o.kind==='nylon'?'#245fd2':o.kind==='washer'?'#158453':'#435d66',
 diagram(o){
   if(o.kind==='spring')return '<svg viewBox="0 0 320 125" role="img" aria-label="两片 A8 碟簧反向串联剖面示意"><rect x="10" y="25" width="35" height="67" fill="#d0e1d4"/><rect x="270" y="25" width="35" height="67" fill="#c1cbd0"/><path d="M85 25 L145 48 M85 92 L145 68 M235 25 L175 48 M235 92 L175 68" stroke="#245fd2" stroke-width="7" fill="none"/><path d="M50 58 H262" stroke="#aab6be" stroke-dasharray="3 3"/><text x="27" y="16" text-anchor="middle">关节侧</text><text x="284" y="16" text-anchor="middle">头侧</text><text x="93" y="114" text-anchor="middle">第 1 片 →</text><text x="230" y="114" text-anchor="middle">← 第 2 片</text><text x="160" y="14" text-anchor="middle">内孔凸边相对</text></svg>';
   const start='<svg viewBox="0 0 320 125" role="img" aria-label="'+(o.kind==='washer'?'垫圈侧面朝向示意':'螺钉从金属螺纹端进入的侧面示意')+'"><defs><marker id="faceSketchArrow" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="none" stroke="#495f65" stroke-width="1.3"/></marker></defs>';
   if(o.kind==='washer')return start+
     '<rect x="234" y="20" width="60" height="70" rx="4" fill="'+(o.metal_only?'#c6d0d4':'#d0e1d4')+'" stroke="#6d897c"/>'+
     '<rect x="143" y="23" width="14" height="66" fill="#b9c3c6" stroke="#6b7d80"/><rect x="140" y="50" width="20" height="12" fill="#f8faf5"/>'+
     '<path d="M157 23 V50 M157 62 V89" stroke="#158453" stroke-width="5"/><path d="M169 35 H222" fill="none" stroke="#495f65" stroke-width="1.5" marker-end="url(#faceSketchArrow)"/>'+
     '<text x="65" y="40" text-anchor="middle">另一面</text><text x="65" y="58" text-anchor="middle">先去毛刺</text><text x="188" y="18" text-anchor="middle" fill="#0d7146">光滑面</text>'+
     '<text x="263" y="51" text-anchor="middle">'+(o.metal_only?'相邻金属':'指定的')+'</text><text x="263" y="69" text-anchor="middle">'+(o.metal_only?'（示意）':'打印件')+'</text>'+
     '<text x="160" y="116" text-anchor="middle">'+(o.metal_only?'此处两面均接触金属，无强制正反':'绿色面贴零件，另一面朝螺钉头／螺母')+'</text></svg>';
   const nylon=o.kind==='nylon';
   return start+'<path d="M130 25 H'+(nylon?'196 L205 33 V48 H122 V33 Z':'185 L193 33 V48 H122 V33 Z')+'" fill="#c1cbd0" stroke="#6f818a"/>'+
     '<path d="M122 64 H'+(nylon?'205 V79 L196 87 H130':'193 V79 L185 87 H130')+' L122 79 Z" fill="#c1cbd0" stroke="#6f818a"/>'+
     (nylon?'<path d="M186 28 H195 L202 34 V48 H186 Z M186 64 H202 V78 L195 84 H186 Z" fill="#245fd2"/>':'')+
     '<path d="M28 56 H286" stroke="#495f65" stroke-width="2" marker-end="url(#faceSketchArrow)"/><text x="59" y="24" text-anchor="middle">螺钉头侧</text><text x="267" y="24" text-anchor="middle">尖端侧</text>'+
     '<text x="61" y="81" text-anchor="middle">旋入 →</text><text x="100" y="114" text-anchor="middle">金属螺纹端</text><text x="239" y="114" text-anchor="middle" fill="'+(nylon?'#245fd2':'#435d66')+'">'+(nylon?'尼龙圈 · 最后穿过':'同样是金属，无尼龙圈')+'</text></svg>';
 }
};
