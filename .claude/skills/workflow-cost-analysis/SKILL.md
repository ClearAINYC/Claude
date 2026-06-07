---
name: workflow-cost-analysis
description: Estimate the cost and ROI of replacing or augmenting a human role/task with a system of AI agents. Use when the user wants to map an enterprise (or personal) workflow, decide what to automate, and calculate the cost/savings/payback of building an agent system. Trigger phrases: "cost of replacing", "automate this workflow", "ROI of agents", "should I automate", "map this process".
---

# Workflow → agent cost analysis (non-developer playbook)

Goal: turn a real workflow into an honest automate/keep-human decision with a dollar figure and payback period. Replace *task-hours*, not whole people — realistic outcome is hybrid (~30% of tasks fully automatable, ~50% need oversight, ~20% stay manual).

## Step 1 — Map the workflow (the highest-value, least-technical part)
Decompose into: **trigger → routing/rules → approvals & handoffs → write-back to systems of record → audit trail.** Note where inputs are structured vs. messy, and where judgment is required.
Rule: **don't automate a broken process** — fix the logic first.

## Step 2 — Screen each task before doing math
- **Automate:** high volume + clear rules + structured inputs.
- **Keep human:** judgment-heavy, low-volume, politically sensitive, or irreversible (spending, legal, live trades).

## Step 3 — Estimate the six inputs

| # | Input | How to get it |
|---|---|---|
| 1 | Automatable hours/month | Time-study the role; flag rule-clear, repetitive tasks |
| 2 | Loaded human cost of those hours | fully-loaded hourly rate × (1) |
| 3 | Model + platform run cost/month | LLM tokens (per-run × volume) + platform sub (e.g. n8n/Make tier) |
| 4 | One-time build cost (amortize /12) | build hrs × rate. Simple rule-based: 2–4 wks; cross-system: 8–16 wks |
| 5 | Oversight cost/month | human-in-the-loop review time (budget 10–30% of freed hours back) |
| 6 | Maintenance/month | APIs break, prompts drift — clients chronically underbudget this |

## Step 4 — Compute
**Net monthly value = (2) − [(3) + (4)/12 + (5) + (6)]**
**Payback (months) = build cost (4) ÷ net monthly value.**
Show the arithmetic explicitly with the user's real numbers.

## Step 5 — Honest verdict
State net savings, payback, and the residual human oversight required. Call out the "oversight tax" — these systems cut headcount-*hours*, they rarely zero out a role. If the automatable share is small or oversight cost is high, say "not worth it" plainly.

## Deliverable
A one-page analysis: the mapped workflow, what's automatable vs. not, the six inputs filled in, the net-value + payback math, and a clear recommendation. If proposing a build, name the platform (default n8n) and the human checkpoints.
