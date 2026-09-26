# Decision

## Decision in one sentence

**Do not buy or build an automated customer follow-up system yet; first run a two-week measurement and use a simple review queue/process for only clearly eligible missing-information follow-ups.**

## Problem and evidence

The narrow problem selected is chasing customers for missing information. Quote approval is outside the selected workflow for this experiment. The pack contains 24 cases and 30 requests. The event export has 128 rows, but only 124 unique event IDs; I deduplicated repeated deliveries before calculating effort. This removes 12 logged minutes that would otherwise be counted twice. The deduplicated log contains 400 coordinator minutes, but it is explicitly incomplete and does not represent all business labour.

Three calculations drive the decision:

| Measure | Result |
|---|---:|
| Exported event rows → unique events | 128 → 124 |
| Duplicate logged effort removed | 12 min |
| Pending missing-information requests → safe follow-up proposals | 12 → 4 |
| Recorded manual reminders | 4 events / 9 min |

A pending request is not treated as proof that an item is missing. Closed/cancelled/scheduled cases are excluded; opted-out records are excluded; already-received items are excluded; requests with missing timing go to review; requests under 48 hours are excluded; conflicting evidence goes to review. Quote-approval requests are excluded because they are outside the selected workflow. On the supplied snapshot this leaves four proposed actions: R009, R024, R025 and R026.

The evidence does **not** validate the owner's eight-hours-per-week estimate. Only nine minutes of explicit reminder effort are recorded in this two-week sample, and the event log is incomplete. A large automation ROI claim is therefore unjustified.

## Alternatives

**Process-only:** maintain a small exception queue reviewed at a fixed cadence. It can use the same deterministic rules implemented in this experiment. This requires no new software or licence and keeps ambiguous cases with a human.

**Existing tool:** Power Automate can run scheduled cloud flows and process lists periodically. Microsoft documents scheduled flows and loop-based processing. Microsoft currently lists Power Automate Premium in India at ₹1,250/user/month, while some Microsoft 365 licences include limited scheduled flows with standard connectors. Actual eligibility depends on Daybreak's existing Microsoft licensing and data location. This is technically feasible, but the available evidence does not establish that a paid licence is necessary or economically justified.

**Build:** a small custom service could implement the same rules, but the supplied evidence shows only four safe missing-information actions in the snapshot. Two engineering weeks should not be spent building infrastructure before actual workload is measured.

## Technical claim and experiment

The consequential claim tested is: **a deterministic rule-based queue can reduce unsafe follow-up candidates within the selected missing-information workflow without treating every pending request as actionable.**

The experiment compares a simple pending-only baseline with the rule-based queue on the same in-scope missing-information requests. The baseline would propose 12 actions; the rules propose four. It also excludes out-of-scope quote approvals and prevents already-received or otherwise ineligible records from becoming proposals.

Verification includes: a stale pending fault-photo record with received evidence (R018) must not become a proposal; a valid no-action condition must produce zero proposals without failing; changing R016's request time from 5 September to 4 September crosses the 48-hour threshold and makes it a proposal; rerunning the experiment produces identical output.

This proves only that the rules behave consistently on this synthetic snapshot. It does not prove response rates or eight hours of savings.

## Net value and next test

For the selected workflow, the strongest measured baseline is four manual reminders consuming nine logged minutes over the observation period. At the observed average of 2.25 minutes per reminder, four equivalent reminders would represent about 9 minutes of gross coordinator effort. That is too small and too uncertain to justify a paid tool or custom build from this sample alone. The missing measurement is actual end-to-end chasing time, including unlogged calls.

The first real-world test should therefore be a two-week measurement: log every customer-chasing action and its active minutes, while using the four-rule queue only as a review aid. **Continue** toward automation only if measured chasing effort is materially higher than the current logged nine minutes and the queue saves at least 25% of that effort without unsafe/duplicate contacts. Otherwise, leave the workflow as a process-only exception queue.
