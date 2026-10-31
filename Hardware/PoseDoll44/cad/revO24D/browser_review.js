async page => {
 const result = await page.evaluate(() => {
  const d = window.O24D, pose = document.querySelector('#pose'), focus = document.querySelector('#focus');
  const change = (el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); };
  const rows = []; let maxPosition = 0, maxRotation = 0;
  for (const name of Object.keys(d.poses)) {
    change(pose, name);
    const f = window.O24D_VIEW_STATE.frames, expected = d.expectedFrames[name];
    let position = 0, rotation = 0;
    for (const [node, matrix] of Object.entries(expected)) {
      position = Math.max(position, Math.hypot(...[0,1,2].map(i => f[node][i*4+3]-matrix[i][3])));
      for (let i=0;i<3;i++) for (let j=0;j<3;j++) rotation=Math.max(rotation,Math.abs(f[node][i*4+j]-matrix[i][j]));
    }
    maxPosition=Math.max(maxPosition,position); maxRotation=Math.max(maxRotation,rotation);
    rows.push({pose:name,frame_count:Object.keys(f).length,max_position_error_mm:position,max_rotation_error:rotation});
  }
  const slider=document.querySelector('[data-axis="l_shoulder_flex"]');
  slider.value='37'; slider.dispatchEvent(new Event('input',{bubbles:true}));
  const manual=window.O24D_VIEW_STATE.pose==='custom' && document.querySelector('#status').textContent.includes('未做');
  change(focus,'wrist'); const filtered=window.O24D_VIEW_STATE.visible>0 && window.O24D_VIEW_STATE.visible<d.parts.length;
  change(focus,'all');change(pose,'neutral');
  const A=window.O24D_VIEW_STATE.angles;
  const ADefault=A.l_shoulder_abduct===45 && A.r_shoulder_abduct===45;
  const bones=d.ueBones.length===89;
  const helperBox=document.querySelector('#helpers');
  const defaultEdges=window.O24D_VIEW_STATE.bone_edge_count, helpersOff=!helperBox.checked;
  helperBox.checked=true;helperBox.dispatchEvent(new Event('change',{bubbles:true}));
  const allEdges=window.O24D_VIEW_STATE.bone_edge_count;
  helperBox.checked=false;helperBox.dispatchEvent(new Event('change',{bubbles:true}));
  const helperToggle=helpersOff && defaultEdges===78 && allEdges===88;
  const wireBox=document.querySelector('#harness'), wireOn=wireBox.checked && window.O24D_VIEW_STATE.harness_spans===d.harness.length && d.harness.length>0;
  wireBox.checked=false;wireBox.dispatchEvent(new Event('change',{bubbles:true}));
  const wireOff=window.O24D_VIEW_STATE.harness_spans===0;
  wireBox.checked=true;wireBox.dispatchEvent(new Event('change',{bubbles:true}));
  change(focus,'electronics');const boardFilter=window.O24D_VIEW_STATE.visible>0 && window.O24D_VIEW_STATE.visible<d.parts.length;
  document.querySelector('[data-view="back"]').click();
  change(focus,'all');document.querySelector('[data-view="three"]').click();
  const gl=document.querySelector('#view').getContext('webgl'), error=gl.getError();
  return {status:maxPosition<1e-7 && maxRotation<1e-10 && manual && filtered && error===0 && ADefault && bones && helperToggle && wireOn && wireOff && boardFilter ? 'PASS':'FAIL',
    geometry_sha256:d.geometry_sha256,parts:d.parts.length,sliders:document.querySelectorAll('[data-axis]').length,
    pose_count:rows.length,path_count:Object.keys(d.paths).length,max_position_error_mm:maxPosition,max_rotation_error:maxRotation,harness_toggle:wireOn&&wireOff,harness_span_count:d.harness.length,electronics_focus:boardFilter,
    manual_unverified_warning:manual,focus_filter:filtered,A_neutral_45_degrees:ADefault,UE_89_bone_overlay:bones,helper_bone_toggle:helperToggle,default_anatomical_edges:defaultEdges,all_UE_edges:allEdges,webgl_error:error,rows,
    scope:'Actual Chrome page: all pose selector change events and JS FK compared with exported Python matrices; manual slider warning and region filtering. Not a physical or continuous collision check.'};
 });
 return result;
}
