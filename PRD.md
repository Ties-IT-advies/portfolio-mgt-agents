# PRD — Portfolio Management Agents (design)

**Status:** Proposal/design for functionality still to be built. No application code exists yet; this document, `docs/`, and `templates/` are the complete Release 1.0 product brief. See `docs/prd/PRD.md` for the full narrative version (problem statement, goals, non-goals, source materials) — this file is the traceable, F-numbered functionality list required by the shared workflow, kept in sync with it.

Part of the Decision Velocity proposition (TiesL & ScripeConnect12). This system covers the *portfolio* governance cycle; the sibling system, Software Development Workflow Agents, covers product/release/sprint/day. Integration between the two is an acknowledged, deferred gap (`docs/decisions/DECISION-LOG.md` — Open Items Carried Forward).

---

## Context

Organizations running project portfolios need consistent, decision-ready information at each governance gate (Idea, Definition, Design, Realization, Go-Live, Closure). Producing and reviewing that information (project briefs, PIDs, status reports, closure reports) is manual, inconsistent in quality, and slow to reach the Portfolio Board or Steering Group. Portfolio Management Agents assess submitted project documentation against a fixed template and process, and give human decision-makers a clear, evidence-based recommendation — without taking the Go/No-Go decision away from them.

---

## Architecture

No implementation exists yet. See `ARCHITECTURE.md` once the first structural decisions (agent runtime, orchestration mechanism, template storage) are made — those are still open (`docs/decisions/DECISION-LOG.md` — Open Items Carried Forward).

Conceptually: one meta-agent orchestrator enforces the linear phase sequence and hands each phase to its own advisor agent (see F1–F6). The orchestrator coordinates; it does not decide (DEC-002 REVISED).

---

## Data source(s)

Not yet defined — this is a specification, not an implementation. Inputs are project documents (idea briefs, PIDs, PSAs, status/closure reports) authored against the templates in `templates/execution-templates.md`; no data store or schema exists yet.

---

## Functionality

### F1 — Project Prioritization Advisor
Scores a project idea against fixed strategic objectives and six operational criteria (operational value, urgency, feasibility, capacity demand, risk manageability, financial impact) on a 1–5 scale, checks portfolio balance, and issues a prioritize / sharpen / do-not-prioritize recommendation. Never decides. Full spec: `docs/prd/agent-specifications.md#project-prioritization-advisor`.

### F2 — Project Idea Advisor
Assesses an early-stage project idea (Idea phase gate) for rationale, objective, coherence, strategic value, sponsorship, and first-order estimates. Classifies each criterion as Sufficient / Point of Attention / Insufficient, and recommends approval, approval with attention points, limited sharpening, or (rarely) not developing further. Full spec: `docs/prd/agent-specifications.md#project-idea-advisor`.

### F3 — Project Brief Advisor
Assesses a completed project brief (Definition phase gate) against the fixed template — project definition, business case, project description — and against strategic objectives, before the Realization decision. Classifies each component as Sufficient / Point of Attention / Insufficient for decision-making. Full spec: `docs/prd/agent-specifications.md#project-brief-advisor`.

### F4 — PID Advisor
Tests a Project Initiation Document (Design phase gate) for completeness (Present / Partially Present / Missing / Not Applicable) and quality, flags findings as Critical / Important / Improvement, and gives a Proceed / Proceed Conditionally / Do Not Proceed Yet recommendation to the Portfolio Board. Full spec: `docs/prd/agent-specifications.md#pid-advisor`.

### F5 — PSA Advisor
Assesses a Project Start Architecture document (Design phase gate, optional review) across eight architecture areas (rationale, business, information/application, NFRs, technical, security, management, decisions/deviations), scoring each Green/Orange/Red/Gray, and gives an Approved / Approved with Conditions / Not Approved recommendation. Full spec: `docs/prd/agent-specifications.md#psa-advisor`.

### F6 — Project Closure Advisor
Assesses a completed project end report (Closure phase gate) for completeness and substantive quality, distinguishes "ready for submission" from "ready for closure," and flags critical blockers (unaccepted products, unmanaged risks, missing handover or board approval). Full spec: `docs/prd/agent-specifications.md#project-closure-advisor`.

### F7 — Meta-Agent Orchestrator
Enforces the strictly linear phase sequence (Idea → Definition → Design → Realization → Go-Live → Closure), maintains cross-phase context, facilitates backward loops to an earlier phase when new information emerges, and escalates impediments it cannot resolve to a human. No phase-skipping, no exception/fast-track paths, and no autonomous decision-making (DEC-001, DEC-002 REVISED). Full spec: `docs/prd/project-lifecycle-flow.md`, `docs/decisions/DECISION-LOG.md`.

### F8 — Execution Templates
Nine primary and two supporting Markdown templates, one per governance artifact (project idea, brief, PID, PSA, status report, closure report, etc.), each role-aware (states its primary role(s)) and phase-mapped, aligned to ScripeConnect12's field-tested framework. English language, checkbox/fill-in-the-blank structure. Full spec: `templates/execution-templates.md`.

---

## Non-functional characteristics

Fifteen subsections, one per characteristic from the register in `nfr/`.
**Answer each subsection with objective reasoning for *this* project — not
with the generic standard assumption (`Standaard`).** "N/A because …" is a valid
answer, provided it's substantiated: the point is that the question is
seriously asked and argued, not that every project must do equally much
everywhere.

<!-- nfr-block:begin — generated by ./generate-prd-block, don't edit by hand -->

### Security
<!-- nfr: spec-security -->
Not yet substantiated — no runtime, no permission model, no secrets exist yet. Open item: role-based access control is explicitly out of scope for Release 1.0 (see Non-Goals in `docs/prd/PRD.md`). Must be answered before implementation starts on any agent that reads real project/financial documents.

### Data integrity
<!-- nfr: spec-data-integrity -->
Not yet substantiated — no data store exists. The one invariant already fixed at the process level: agents never overwrite a human decision (DEC-001) and the Decision Log itself is append-only (superseded entries are marked, never deleted — see `docs/decisions/DECISION-LOG.md`'s own convention).

### Failure modes
<!-- nfr: spec-failure-modes -->
Partially substantiated at the process level: every advisor agent is specified to explicitly name missing/contradictory/unreadable input rather than guess or invent data (see each agent's "Error Handling and Limitations" in `docs/prd/agent-specifications.md`), and the orchestrator escalates impediments it cannot resolve to a human rather than stalling silently (F7). Technical failure modes (agent runtime crash, template corruption, API timeouts) are N/A until an implementation exists.

### Observability
<!-- nfr: spec-observability -->
Not yet substantiated — no runtime to observe.

### Performance and scale
<!-- nfr: spec-performance-scale -->
Not yet substantiated. Expected usage is bounded by an organization's own portfolio size (tens, not millions, of concurrent projects) — no scale concerns anticipated, but not yet tested against a real deployment.

### Deployability
<!-- nfr: spec-deployability -->
Not yet substantiated — no environments exist yet.

### Privacy
<!-- nfr: spec-privacy -->
Not yet substantiated. Project documentation processed by the agents may name individuals (sponsors, project managers, stakeholders) in a business context; no special categories of personal data are anticipated. Needs a real answer once a storage/runtime choice is made.

### Compliance and auditability
<!-- nfr: spec-compliance -->
Partially substantiated at the process level: DEC-001 requires every Go/No-Go to remain a human action, and agent assessments plus human decisions are intended to form an audit trail (see Entry 1, "Roadmap Implication," `docs/decisions/DECISION-LOG.md`). No legal/regulatory retention obligation identified yet — organizations adopting this system may have their own.

### Backup and recovery
<!-- nfr: spec-backup-recovery -->
Not yet substantiated — no data store exists.

### Portability
<!-- nfr: spec-portability -->
Not yet substantiated — no platform choice has been made.

### Maintainability
<!-- nfr: spec-maintainability -->
Partially substantiated by design: each advisor agent is a separate, independently specified unit bound to one governance phase (F1–F6), coordinated but not merged into a single unified agent (DEC-002 REVISED, Option C chosen over a single unified agent specifically for this separation — see Entry 2 REVISED). Templates (F8) are likewise a separate, versioned artifact from the agent specs.

### Testability
<!-- nfr: spec-testability -->
Not yet substantiated — no code exists. Each agent's spec already defines a fixed step-by-step evaluation process and execution format (`docs/prd/agent-specifications.md`), which should translate directly into test scenarios once implementation starts.

### Usability
<!-- nfr: spec-usability -->
Partially substantiated: outputs are specified to be role-aware and decision-focused (executive summaries capped at 10-150 words depending on the agent, prioritized findings, explicit recommendation) so a Portfolio Board or Steering Group member can act on them without additional interpretation. Full detail per agent in `docs/prd/agent-specifications.md`.

### Cost control
<!-- nfr: spec-cost-management -->
Not yet substantiated — no runtime or API usage exists yet.

### Documentation
<!-- nfr: spec-documentation -->
`docs/prd/PRD.md` (narrative), `docs/decisions/DECISION-LOG.md` (why), `docs/prd/agent-specifications.md` (agent behavior), `docs/prd/project-lifecycle-flow.md` (process), `docs/decisions/roles-and-personas.md` (who), and `templates/execution-templates.md` (artifacts) are the current source of truth and are updated as decisions are made (see "Updating the Decision Log" convention). This file (`PRD.md`) is the traceability layer required by the shared workflow and must be kept in sync with `docs/prd/PRD.md` as functionality is added.
<!-- nfr-block:end -->

---

## Out of scope

- Autonomous Go/No-Go decision-making by agents (deferred to a 2.0+ roadmap — DEC-001).
- Phase-skipping or exception-path routing (excluded by design — DEC-002 REVISED).
- Role-based access control / permissions model (open item, not yet specified).
- Integrations with external HR/Finance/PM systems (open item, not yet specified).
- Integration with the sibling Software Development Workflow Agents system (acknowledged, deferred gap).

## Known limitations

What the system deliberately doesn't do or can't do. Stays this way unless
the scope changes — no action needed.

- No application code exists yet — this whole repository is a specification for a Release 1.0 system still to be built.
- `docs/prd/PRD.md` and `docs/decisions/DECISION-LOG.md` reference original Dutch-language field documents from co-founder ScripeConnect12 under `reference/scripeconnect12-source-materials/`. That directory was deliberately never added to this repository (not needed going forward, and not appropriate to publish) — those references are historical pointers, not a missing deliverable.

## Technical debt

What you'd build differently if you started over: incidental complexity,
deliberate shortcuts, outdated dependencies, missing tests. Accepted review
findings land here too. See *Complexity, technical debt, refactoring* in
`CLAUDE.md`.

| What | Why acceptable for now | Trigger to address it |
|---|---|---|
| Two PRD documents (`PRD.md` at root, `docs/prd/PRD.md`) covering the same product from different altitudes | `docs/prd/PRD.md` is the original narrative brief (problem/goals/non-goals); root `PRD.md` is the workflow's F-numbered traceability layer, generated from it. Duplication is deliberate during the spec phase. | Once implementation starts and `TEST-SCENARIOS.md`'s `Covers:` fields reference this file's F-numbers, fold any content that has drifted between the two back into a single source, or make the relationship (which one is normative) explicit here. |

---

## Project files

| File | Purpose |
|---|---|
| `docs/prd/PRD.md` | Narrative product brief: problem statement, goals, non-goals, system overview, open questions. |
| `docs/decisions/DECISION-LOG.md` | Dated log of product/architecture decisions, options considered, and rationale. Append-only; superseded entries are marked, not deleted. |
| `docs/decisions/roles-and-personas.md` | The eleven functional human roles across four governance tiers. |
| `docs/prd/agent-specifications.md` | Full behavioral spec for each of the six advisor agents (F1–F6). |
| `docs/prd/project-lifecycle-flow.md` | The six-phase governance flow and gate structure (F7). |
| `docs/diagrams/project_flow_diagram.mermaid` / `.html` | Visual rendering of the lifecycle flow. |
| `templates/execution-templates.md` | Index linking to the nine primary + two supporting Markdown governance templates, each in its own file (F8). |
| `CONTEXT.md` | Project jargon glossary (PID, PSA, Portfolio Board, DEC-XXX, etc.), separate from `ARCHITECTURE.md`'s structural decisions. |
