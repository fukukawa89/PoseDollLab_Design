import json
import o22f6_holeclear as h
rows=[]
for group in ['wall_trials','feature_trials','phase_trials','relief_trials','tip_trials','tilt_trials']:
 for fp in (h.WORK/group).rglob('result.json'):
  q=json.loads(fp.read_text());rows.append(dict(group=group,candidate=str(fp.parent.relative_to(h.WORK)),result=q,adopted_in_delivery=False))
h.put(h.WORK/'rejected_experiment_summary.json',dict(scope='Independent trials only. None of the body-modifying, wall-generator, feature-threshold, layer-phase, rigid-tilt or tilt-routing experiments listed here was adopted in O22F6_HoleClear. Final body-array hashes independently confirm identity with F5.',trials=rows))
print('FAILED_TRIAL_RECORDS',len(rows))