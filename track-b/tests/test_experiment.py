import csv
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]


class ExperimentChecks(unittest.TestCase):
    def run_experiment(self):
        p = subprocess.run(
            [sys.executable, str(ROOT / "experiment.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        with (ROOT / "output" / "experiment_queue.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        return rows, p.stdout

    def test_expected_baseline_and_proposals(self):
        rows, out = self.run_experiment()
        self.assertIn("Pending missing-information baseline: 12", out)
        self.assertIn("Rule-based proposed actions: 4", out)
        self.assertEqual(sum(r["action"] == "PROPOSE" for r in rows), 4)

    def test_stale_pending_received_evidence_is_excluded(self):
        rows, _ = self.run_experiment()
        r = next(x for x in rows if x["request_id"] == "R018")
        self.assertEqual(r["action"], "EXCLUDE")
        self.assertIn("received", r["reason"])

    def test_quote_approval_is_out_of_scope(self):
        rows, _ = self.run_experiment()
        r = next(x for x in rows if x["request_id"] == "R027")
        self.assertEqual(r["action"], "EXCLUDE")
        self.assertIn("outside selected", r["reason"])

    def test_no_action_input_is_safe(self):
        import experiment

        cases = experiment.load_csv("cases.csv")
        events = list(
            {e["event_id"]: e for e in experiment.load_csv("events.csv")}.values()
        )
        req = {
            "request_id": "NOACTION",
            "case_id": "C001",
            "item": "fault_photo",
            "status": "pending",
            "last_requested_at": "2026-08-24T10:00:00+05:30",
            "followup_allowed": "1",
            "received_at": "",
        }
        action, _ = experiment.classify({c["case_id"]: c for c in cases}, events, req)
        self.assertEqual(action, "EXCLUDE")

    def test_changed_input_effect(self):
        # R016 is 46h old in the supplied snapshot. Moving its request time
        # back by 24h should cross the 48h threshold and make it eligible.
        import experiment

        req = {
            "request_id": "R016",
            "case_id": "C016",
            "item": "fault_photo",
            "status": "pending",
            "last_requested_at": "2026-09-04T11:00:00+05:30",
            "followup_allowed": "1",
            "received_at": "",
        }
        cases = experiment.load_csv("cases.csv")
        events = list(
            {e["event_id"]: e for e in experiment.load_csv("events.csv")}.values()
        )
        action, reason = experiment.classify({c["case_id"]: c for c in cases}, events, req)
        self.assertEqual(action, "PROPOSE")
        self.assertIn(">=48h", reason)

    def test_rerun_is_idempotent(self):
        rows1, _ = self.run_experiment()
        rows2, _ = self.run_experiment()
        self.assertEqual(rows1, rows2)


if __name__ == "__main__":
    unittest.main()
