"""Daybreak Repairs Track B experiment.
Python 3.10+, standard library only.

Tests the claim that a deterministic rule set can safely narrow a customer-follow-up
queue within the selected missing-information workflow, without treating every
pending request as actionable.
"""
import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "output"
SNAPSHOT = datetime.fromisoformat("2026-09-07T09:00:00+05:30")
MISSING_INFO_ITEMS = {"fault_photo", "serial_number", "site_access"}


def load_csv(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_dt(value):
    return datetime.fromisoformat(value) if value else None


def classify(case_by_id, events, req):
    # The selected workflow is collecting missing information. Quote approval
    # requests are intentionally out of scope for this experiment.
    if req["item"] not in MISSING_INFO_ITEMS:
        return "EXCLUDE", "outside selected missing-information workflow"

    case = case_by_id[req["case_id"]]
    status = case["status"]
    if status in {"completed", "cancelled", "scheduled"}:
        return "EXCLUDE", "case closed or already scheduled"
    if req["followup_allowed"] != "1":
        return "EXCLUDE", "follow-up not allowed"
    if req["received_at"]:
        return "EXCLUDE", "item already recorded as received"
    if not req["last_requested_at"]:
        return "REVIEW", "missing request time"
    hours = (SNAPSHOT - parse_dt(req["last_requested_at"])).total_seconds() / 3600
    if hours < 48:
        return "EXCLUDE", "less than 48 hours"
    if req["status"] != "pending":
        return "REVIEW", "request state is not pending"
    if req["item"] == "fault_photo":
        reply_for_case = any(
            e["case_id"] == req["case_id"] and e["event_type"] == "customer_reply"
            for e in events
        )
        if reply_for_case:
            return "REVIEW", "pending status conflicts with reply evidence"
    return "PROPOSE", "pending, follow-up allowed, item not received, >=48h"


def run():
    cases = load_csv("cases.csv")
    events_raw = load_csv("events.csv")
    requests = load_csv("requests.csv")

    # Deduplicate by stable event identity.
    events = {}
    for e in events_raw:
        events[e["event_id"]] = e
    events = list(events.values())
    case_by_id = {c["case_id"]: c for c in cases}

    results = []
    for r in requests:
        action, reason = classify(case_by_id, events, r)
        results.append({
            "request_id": r["request_id"],
            "case_id": r["case_id"],
            "item": r["item"],
            "action": action,
            "reason": reason,
        })

    OUT.mkdir(exist_ok=True)
    with (OUT / "experiment_queue.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    proposals = sum(
        r["action"] == "PROPOSE" for r in results
    )
    baseline = sum(
        r["status"] == "pending" and r["item"] in MISSING_INFO_ITEMS
        for r in requests
    )
    exported_minutes = sum(float(e["active_minutes"] or 0) for e in events_raw)
    unique_minutes = sum(float(e["active_minutes"] or 0) for e in events)
    quote_approval_requests = sum(r["item"] == "quote_approval" for r in requests)

    summary = {
        "snapshot": SNAPSHOT.isoformat(),
        "cases": len(cases),
        "exported_event_rows": len(events_raw),
        "unique_event_ids": len(events),
        "duplicate_event_rows_removed": len(events_raw) - len(events),
        "duplicate_logged_minutes_removed": exported_minutes - unique_minutes,
        "unique_logged_coordinator_minutes": unique_minutes,
        "pending_requests_overall": sum(r["status"] == "pending" for r in requests),
        "quote_approval_requests_out_of_scope": quote_approval_requests,
        "pending_missing_information_requests": baseline,
        "safe_followup_proposals": proposals,
        "manual_reminder_events": sum(
            e["event_type"] == "reminder" for e in events if e["event_type"]
        ),
        "manual_reminder_minutes": sum(
            float(e["active_minutes"] or 0)
            for e in events
            if e["event_type"] == "reminder"
        ),
    }
    with (OUT / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    print(f"Snapshot: {SNAPSHOT.isoformat()}")
    print(f"Exported events: {len(events_raw)}; unique event IDs: {len(events)}")
    print(f"Pending missing-information baseline: {baseline}")
    print(f"Rule-based proposed actions: {proposals}")
    print(f"Suppressed from action: {baseline - proposals}")
    return results


if __name__ == "__main__":
    run()
