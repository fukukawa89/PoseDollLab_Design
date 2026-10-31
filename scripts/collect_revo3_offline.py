"""Collect only successful sealed offline producers; no inferred hardware pass."""
from revo3_evidence import *
def main():
 v,o=run_paths();receipts={}
 for name in ('compatibility','legacy_config','python_tests','host_C','golden_crosscheck'):
  r=ArtifactReader(name);r.path(v/(name+'.txt'));receipts[name]=r.receipt()
 save(v/'offline.json',{'status':'PASS','consumed_inputs':receipts,'scope':'Python regressions and C core/gateway/session models plus fresh binary wire crosscheck','physical_tested':False})
if __name__=='__main__':main()
