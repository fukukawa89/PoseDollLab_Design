"""Account for actual single-unit landed quotations; missing fields are not zero."""
import json,math,argparse
from pathlib import Path
B=Path(__file__).resolve().parent.parent

def check(data):
 budget=json.loads((B/'budget.json').read_text(encoding='utf-8-sig'));required={r['id'] for r in budget['rows'] if r['id']!='reserve'}
 rows=data.get('items',[])
 if {r.get('id') for r in rows}!=required or len(rows)!=len(required):raise ValueError('complete, unique budget categories required')
 total=0
 for row in rows+data.get('additional_mandatory_costs',[]):
  n=row.get('landed_total_cny')
  if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<0:raise ValueError('missing/invalid actual price: '+str(row.get('id')))
  if not row.get('quote_reference') or row.get('confirmed') is not True:raise ValueError('unconfirmed quote: '+str(row.get('id')))
  if row.get('includes_tax_moq_processing_freight') is not True:raise ValueError('landed scope incomplete')
  if n==0 and not row.get('zero_cost_reason'):raise ValueError('zero cost needs explanation')
  total+=n
 reserve=data.get('retained_reserve_cny')
 if isinstance(reserve,bool) or not isinstance(reserve,(int,float)) or not math.isfinite(reserve) or reserve<0:raise ValueError('explicit reserve required')
 return {'actual_quoted_landed_cny':round(total,2),'including_reserve_cny':round(total+reserve,2),'target_cny':1500,'within_target':total+reserve<=1500,'hardware_qualified':False,'quote_authenticity':'Requires human verification against supplied quotation.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('quotes');a=p.parse_args();print(json.dumps(check(json.loads(Path(a.quotes).read_text(encoding='utf-8-sig'))),ensure_ascii=False,indent=2))
