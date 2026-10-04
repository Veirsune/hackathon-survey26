"""Public feedback gates for earlier free diagnosis after pointing recovery."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_core.report_budget import budgeted_report, early_free_diagnostic


class ReportingTests(unittest.TestCase):
    def planner(self, ratio=.3):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        rows = [(float(t), night, ratio) for night, times in
                ((9, (226, 227, 228)), (10, (248, 249, 250))) for t in times]
        state = SimpleNamespace(false_report_free_allowance=2, survey_start=start,
            force_program=None, notices={"earthquake|ALL"}, _earthquake_seen_hours=120.,
            nights=[(start+timedelta(hours=260+n*24), start+timedelta(hours=268+n*24)) for n in range(5)],
            clean_history=[(float(n), 0, 1.) for n in range(40)],
            _diagnostic_exposures=list(rows), _weather_clear_diagnostic_exposures=list(rows),
            forget_quality_history=lambda: None)
        mount = SimpleNamespace(history=[(0., 0., [0]*8)]*3,
                                offset=(0., 0.), errors=lambda offset: 0)
        return SimpleNamespace(state=state, mount=mount, _false_since_correct=0,
            _last_false_hours=0., _last_false_ratio=.65, last_report_hours=0., reports=0,
            _await_report_result=False, suspicion_hours=[], log=lambda *_: None,
            _baseline_report=lambda *_: None)

    def test_evidence_allows_earlier_free_report_but_not_paid_report(self):
        p = self.planner()
        self.assertEqual(budgeted_report(p, 250., {})['action'], 'report')
        self.assertEqual(p.reports, 1)
        p = self.planner()
        p._false_since_correct = 2
        self.assertIsNone(budgeted_report(p, 250., {}))

    def test_time_window_and_consistent_pointing_are_required(self):
        p = self.planner()
        self.assertTrue(early_free_diagnostic(p, 250., False))
        for hour in (210., 300.):
            self.assertFalse(early_free_diagnostic(p, hour, False))
        p.mount.errors = lambda offset: 2
        self.assertFalse(early_free_diagnostic(p, 250., False))

    def test_weather_and_missing_clear_history_block_early_report(self):
        p = self.planner()
        p.state.notices.add('haze|NW')
        self.assertIsNone(budgeted_report(p, 250., {}))
        p = self.planner()
        p.state._weather_clear_diagnostic_exposures=[]
        self.assertIsNone(budgeted_report(p, 250., {}))

    def test_early_path_requires_stronger_drop_than_normal_free_path(self):
        p = self.planner(ratio=.6)
        self.assertIsNone(budgeted_report(p, 250., {}))
        p.state._earthquake_seen_hours = 0.
        self.assertEqual(budgeted_report(p, 250., {})['action'], 'report')


if __name__ == '__main__':
    unittest.main()
