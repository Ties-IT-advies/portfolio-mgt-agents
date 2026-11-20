# Decision Log — Portfolio Management Agents

This log records the product/architecture decisions made during specification of the Portfolio Management Agents system, including the options considered and the rationale for each choice. It is the single source of truth for "why is it built this way" — consult it before proposing changes that would contradict a logged decision, and add a new entry (don't silently overwrite) when a decision is revisited.

Detailed role and persona definitions referenced in Entry 3 live in [`roles-and-personas.md`](./roles-and-personas.md).

---

## Entry 1

**Decision ID:** DEC-001
**Topic:** Agent Decision-Making Authority & Scope
**Status:** Approved (Release 1.0)

**Decision Made:**
Option C — Assessment + Modification Rights (with phased autonomy approach)

**Options Considered:**
- Option A: Assessment & Recommendation Only
- Option B: Assessment + Automated Decisions (Defined Rules)
- **Option C: Assessment + Modification Rights** → CHOSEN
- Option D: Custom approach

**Rationale:**
In Release 1.0, human decision-makers retain all Go/No-Go authority. Agents document project facts and status both:
- **Prior to decisions:** comprehensive assessment and recommendations provided to humans
- **Subsequent to decisions:** agents update project status/metadata in the system based on human-approved decisions

This approach:
1. Preserves human authority in decision-making (critical for governance)
2. Automates documentation & status tracking (reduces manual work)
3. Creates an audit trail and single source of truth for project data
4. Positions for future releases where agents can make autonomous decisions within defined, pre-approved boundaries

**Roadmap Implication:** Future releases (2.0+) can progressively grant decision autonomy for low-risk scenarios (e.g., auto-approve projects scoring above a threshold with all criteria met).

---

## Entry 2 (Superseded — see Entry 2 REVISED below)

**Decision ID:** DEC-002
**Topic:** Agent Architecture & Coordination
**Status:** Superseded by Entry 2 (REVISED)

**Decision Made (original):**
Option C — Specialized Meta-Agent + Phase Agents (with bounded orchestration, permitting phase-skipping for defined "tier" scenarios: New Product / New Release / New Feature)

This version allowed phase skipping under specific documented scenarios and framed exception paths as available but non-liberal. It was corrected immediately after logging — see the revised entry — once it was clarified that the Portfolio Management Agents system (unlike the separate Software Development Workflow system) must be strictly linear with no phase skipping or exception paths at all. Kept here for traceability only; **do not implement against this version.**

---

## Entry 2 (REVISED)

**Decision ID:** DEC-002
**Topic:** Agent Architecture & Coordination
**Status:** Approved (Release 1.0)

**Decision Made:**
Option C — Specialized Meta-Agent + Phase Agents (strictly linear process)

**Options Considered:**
- Option A: Independent Agents, Sequential Flow
- Option B: Coordinated Agent System with Shared Context
- **Option C: Specialized Meta-Agent + Phase Agents** → CHOSEN
- Option D: Single Unified Agent with Phase-Specific Modes
- Option E: Custom approach

**Rationale:**
A meta-agent orchestrator provides intelligent coordination and context management while maintaining strict adherence to a linear process flow.

**Guardrails & Constraints:**

1. **Process Flow: STRICTLY LINEAR**
   - Fixed sequence: Idea → Definition → Design → Realization → Go-Live → Closure
   - NO phase skipping under any circumstances
   - NO exception paths — all projects follow the same sequence

2. **Looping Back (Revisit Earlier Phases): FACILITATED**
   - When new insights emerge during later phases, the orchestrator can request earlier-phase reconsideration
   - Example: Design phase identifies an issue; can route back to Definition for clarification
   - This is the only flexibility mechanism in Release 1.0

3. **Escalation to Humans:** when routing/coordination decisions exceed orchestrator logic, escalate to governance (Portfolio Board / Steering Group per [project-lifecycle-flow.md](../prd/project-lifecycle-flow.md))

**Implication for Architecture:**
- The meta-agent is a process manager/coordinator, not a decision-maker
- It enforces linear flow, maintains context, routes backward when needed, and escalates impediments
- Contrast with the separate Software Development Workflow Agents system (product/release/sprint cycle), which *is* permitted phase-skipping, exception paths and non-linear looping — that flexibility model does not apply here

---

## Entry 3

**Decision ID:** DEC-003
**Topic:** Primary End Users & Roles
**Status:** In Development (Release 1.0)

**Decision Made:**
Role structure organized into four tiers, aligned with ScripeConnect12's portfolio governance framework (`reference/scripeconnect12-source-materials/Portfolio Management Rolbeschrijvingen.rtf`):

- **Portfolio Board Tier** (strategic): Portfolio Owner, Business Owner/Division Head, CFO, Portfolio Manager (optional)
- **Steering Group Tier** (project execution oversight): Project Sponsor (Opdrachtgever), Senior User, Senior Supplier
- **Execution Tier** (day-to-day delivery): Project Manager, Project Team/SME
- **Supporting Roles**: Financial/Resource Manager, Organizational Administrator

Full role descriptions (who they are, when they interact, what they need from the system) are documented in [`roles-and-personas.md`](./roles-and-personas.md).

**Rationale:**
- Portfolio Board composition reflects ScripeConnect12's model: Portfolio Owner (executive sponsor), Business Owners (divisional representation), CFO (financial governance)
- Steering Group structure follows ScripeConnect12's standard PRINCE2-style model: Opdrachtgever, Senior User, Senior Supplier
- The three governance tiers (Portfolio Board → Steering Group → Execution) preserve clear accountability and decision authority at each level
- Role descriptions define functional needs, not job titles — organizations of any size can combine or split roles as needed
- Client-specific examples from ScripeConnect12's source material were generalized/removed from our documentation

**Status:** Role structure is defined; open questions on advisor-vs-user role separation, access/permission model, and role-specific dashboards remain tracked in `roles-and-personas.md` under "Questions for Refinement."

---

## Entry 4

**Decision ID:** DEC-004
**Topic:** Execution Template Alignment with ScripeConnect12's Framework
**Status:** Approved (Release 1.0)

**Decision Made:**
Align all execution templates with the structure and content of the templates ScripeConnect12 provided (`reference/scripeconnect12-source-materials/templates/`), while:
- Keeping Markdown format (not Word/PowerPoint)
- Keeping English language only
- Keeping checkbox/checklist/fill-in-the-blank structure
- Making every template role-aware (explicit "Primary Roles" designation)
- Creating new Markdown versions of ScripeConnect12's templates that we didn't previously have

**Options Considered:**
- Keep our original generic templates unchanged — Denied
- Adopt ScripeConnect12's templates as-is in Word/PowerPoint format — Denied (format/language requirements)
- **Align content/structure with ScripeConnect12's templates, rebuild in Markdown, English, role-aware — CHOSEN**

**Rationale:**
ScripeConnect12's templates reflect real, field-tested governance documents already in use. Aligning our system's templates to that structure means the tool produces artifacts that plug directly into an organization's existing governance process rather than introducing a parallel, incompatible format. Markdown was retained (over replicating Word/PowerPoint) because it is the native format for agent-generated output and version control.

**Result:** `templates/execution-templates.md` contains 9 primary templates + 2 supporting templates, each mapped to a lifecycle phase and to the primary role(s) who use it. New templates created to cover gaps versus ScripeConnect12's set: Project Brief, Project Initiation Document (PID), Project Start Architecture, Go/No-Go Decision, Change Request.

**Note:** All client-specific references present in ScripeConnect12's source material were removed from our derived documentation, per explicit instruction.

---

## Entry 5

**Decision ID:** DEC-005
**Topic:** Execution Templates File Structure
**Status:** Approved

**Decision Made:**
Split `templates/execution-templates.md`'s 11 templates into one standalone `.md` file per template, named after the template itself. Keep `execution-templates.md` as an index/table of contents linking to the 11 files, rather than deleting it.

**Options Considered:**
- Leave all 11 templates bundled in one file — Denied (harder to read/edit/reference a single template independently as the system grows)
- Split into 11 files and delete `execution-templates.md` — Denied (every existing cross-reference in `README.md`, `PRD.md`, `docs/prd/PRD.md`, and this log points at `templates/execution-templates.md` as *the* template set; deleting it would break all of them for no benefit, since none of those references single out one template)
- **Split into 11 files, keep `execution-templates.md` as an index — CHOSEN**

**Rationale:**
Splitting makes each template independently readable/editable/referenceable. Keeping the original file as an index means every existing "the templates live at `templates/execution-templates.md`" reference in this repo remains correct as written — it's now the entry point into the set rather than the set itself, with no cross-reference rewrites required.

**Filename note:** Template 7's actual name contains a `/` ("Go/No-Go Decision Template"), which cannot be a literal filename component. Confirmed with TiesL: the file is `Go_No-Go Decision Template.md` (underscore replacing the slash); the index and every reference display the real name with the slash, only the filename itself substitutes it.

**Result:** `templates/` now contains `execution-templates.md` (index) plus 11 standalone template files. Content was moved verbatim; only the per-template heading level/numbering (`## N. Name` → `# Name`) and the file's own dangling trailing separators were normalized, since those were artifacts of the bundled file, not template content.

---

## Entry 6

**Decision ID:** DEC-006
**Topic:** Project Idea Template v12 — Field Registry, Locale Design, and Checklist Removal
**Status:** Approved

**Decision Made:**
Promote the Project Idea Submission Template to v12 by adding three fields (`strategic_contribution`, `departments_involved`, `complexity`); establish `skill/idea-gate/fields.yaml` and `skill/idea-gate/locales/{en,nl}.yaml` as the single source of truth for all field metadata; rebuild the Markdown template to mirror the Word template field-for-field; drop the old checklist.

**Rationale:**

- **v12 fields.** Three fields absent from the v9 Word template were added per the Saga 1 Problem section: strategic contribution (connects the idea to the Strategic Assessment Framework), departments involved (required for classification when more than one department is affected), and complexity (supports early feasibility assessment). The 9 v9 fields are unchanged.
- **Registry + locales.** `fields.yaml` lists every field with its id, section, versions, and English guidance. `locales/en.yaml` and `locales/nl.yaml` hold labels and guidance per language. Downstream work (assessment rubric, `.docx` fixtures, localization) reads from the registry — labels are never hard-coded elsewhere.
- **"Mirrors" replaces "aligned with".** The Markdown template now matches the Word template field-for-field. This refines DEC-004's weaker claim that our template was "aligned with" ScripeConnect12's format.
- **Checklist dropped.** The prior template used a reviewer checklist format, not a submitter form, and contained fields absent from the Word template. It was replaced because it modelled the wrong actor and misled anyone trying to use it as a fill-in document.
- **v9 compatibility.** Fields tagged `[v9, v12]` exist in both versions; fields tagged `[v12]` are new. The system recognizes both.

**Options Considered:**
- Add three checklist items to the existing template — Denied (wrong actor model; misaligns with the Word template)
- Add three fields directly to the Markdown template without a registry — Denied (downstream work would hard-code labels)
- **Registry + locale design with v12 Markdown template rebuild — CHOSEN**

---

## Entry 7

**Decision ID:** DEC-007
**Topic:** Separation of `./check` (offline) and `./eval` (model-driven)
**Status:** Approved

**Decision Made:**
`./check` is the CI gate: offline, deterministic, runs on every PR. It covers scripts, validators, and committed fixtures, but never calls the model. `./eval` is the separate evaluation harness: invokes Claude Code headless on every `.docx` fixture, validates each result against the schema validator, and reports a V1 pass rate. `./eval` is run by the Portfolio Manager; it is never invoked by CI.

**Rationale:**
- **No API key in CI.** Calling the model from CI would require a stable API key in the repo or secrets, introduce non-determinism, and add latency/cost to every PR check.
- **Separation of concerns.** `./check` answers "is the code correct?"; `./eval` answers "does the skill produce valid output on real fixtures?". These are different questions on different cadences.
- **Verification path for V1 and V4.** V1 (KR 1.2 — every field rated with quoted evidence) and V4 (KR 1.3 — repeat runs for stability) are both verified by running `./eval`, not by CI. The Portfolio Manager runs `./eval` after meaningful skill changes.

**Implications:**
- `./check` and `.github/workflows/ci.yml` must not call `./eval`.
- `./eval --runs N` stores N result sets per fixture in `.eval-out/<timestamp>/`; comparison logic is out of scope for V1 (deferred to KR 1.3).
- KR 1.2 is verified via `./eval`, not via a CI status check.

---

## Open Items Carried Forward

These are not yet decided and should be resolved before or during early development:

1. Advisor roles vs. end-user roles — do the six portfolio advisor roles (Project Idea Advisor, Project Brief Advisor, PID Advisor, PSA Advisor, Project Closure Advisor, Project Prioritization Advisor — see `agent-specifications.md`) need distinct system representation from the human end-user roles in `roles-and-personas.md`?
2. External stakeholders (clients, vendors, regulatory bodies) — in scope for Release 1.0 or deferred?
3. Portfolio Manager role necessity — when is this a dedicated position vs. folded into Portfolio Owner/PMO?
4. Role-based access/permission model — not yet specified.
5. Integration points with external systems (HR, Finance, PM tooling) — not yet specified.
6. Relationship/integration touchpoints with the separate Software Development Workflow Agents system (different cadence: portfolio cycle vs. product/release/sprint/day cycle) — acknowledged as a gap, deferred.
