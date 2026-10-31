"""JST SH catalog compatibility only; never a crimp/current/lifetime qualification."""
from pathlib import Path
import json, unittest
ROOT=Path(__file__).resolve().parent

def catalog_compatible(awg: int, insulation_od_mm: float) -> bool:
    if type(awg) is not int or type(insulation_od_mm) not in (int,float):
        raise TypeError('Expected integer AWG and numeric insulation OD')
    return 28 <= awg <= 32 and .4 <= insulation_od_mm <= .8

class ContractTests(unittest.TestCase):
    def test_26_not_applicable(self): self.assertFalse(catalog_compatible(26,.8))
    def test_28_applicable_range_only(self): self.assertTrue(catalog_compatible(28,.8))
    def test_30_applicable_range_only(self): self.assertTrue(catalog_compatible(30,.6))
    def test_insulation_too_large(self): self.assertFalse(catalog_compatible(28,1.0))
    def test_too_small_conductor(self): self.assertFalse(catalog_compatible(34,.4))

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/connector_contract.json').write_text(json.dumps({'source':'JST eSH.pdf p2','part':'SSH-003T-P0.2-H','tests_run':r.testsRun,'errors':len(r.errors),'failures':len(r.failures),'26_AWG_catalog_compatible':False,'28_AWG_catalog_compatible_with_0p8mm_OD':True,'physical_qualification':False},indent=2)+'\n')
    raise SystemExit(0 if r.wasSuccessful() else 1)
