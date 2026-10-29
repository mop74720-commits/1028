"""Acceptance checks on the delivered new numerical runs, not old frozen data.

Regenerate with run_integrators.py and run_birkhoff.py before using this test
on an intentionally empty results tree. Missing outputs fail, rather than skip.
"""
from pathlib import Path
import json
import unittest

RESULTS=Path(__file__).resolve().parents[1]/'results'

class NumericalEvidence(unittest.TestCase):
    def test_local_chart_converges_to_its_actual_field(self):
        r=json.loads((RESULTS/'birkhoff/results_T0.0005.json').read_text())
        self.assertEqual(r['status'],'completed')
        self.assertEqual(len(r['rows']),6)
        self.assertEqual(len(r['references']),4)
        self.assertTrue(all(v['nfev']>0 for v in r['references']))
        for method in ('original_midpoint','birkhoff_chart_midpoint'):
            row=[v for v in r['rows'] if v['method']==method][-1]
            self.assertGreater(row['observed_order_to_integrated_field'],1.8)
            self.assertLess(row['observed_order_to_integrated_field'],2.2)
            self.assertLessEqual(row['residual_inf'],r['solver_tolerance'])
        row=[v for v in r['rows'] if v['method']=='birkhoff_chart_midpoint'][-1]
        self.assertLess(row['first_step']['first_step_Ka_defect_2'],1e-11)
        self.assertLess(r['represented_reference_refinement_max'],row['error_to_represented_max']*1e-3)
        # A small structural defect must not hide the large represented-field error.
        self.assertGreater(row['error_to_original_max'],100*row['error_to_represented_max'])

    def test_long_window_is_not_reported_as_success(self):
        r=json.loads((RESULTS/'birkhoff/results_T0.004.json').read_text())
        self.assertEqual(r['status'],'interrupted_due_to_diagnosed_transport_truncation_failure')
        self.assertEqual(r['rows'],[])
        self.assertEqual(len(r['references']),2)

    def test_common_rom_and_initial_state(self):
        b=json.loads((RESULTS/'birkhoff/results_T0.0005.json').read_text())
        i=json.loads((RESULTS/'integrators/integrators.json').read_text())
        self.assertEqual(b['initial_state'],i['initial_state'])
        self.assertEqual(b['model']['q_dof'],12)
        self.assertEqual(b['model']['quadrature_elements'],20)
        self.assertEqual(b['model']['mass'],i['model']['mass'])

if __name__=='__main__':unittest.main(verbosity=2)
