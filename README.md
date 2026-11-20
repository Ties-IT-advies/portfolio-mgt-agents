# Portfolio Management Agents

Part of the **Decision Velocity** proposition (TiesL & ScripeConnect12). This repository is the specification and starting point for building an agent-based portfolio governance system: a strictly linear, six-phase project lifecycle (Idea → Definition → Design → Realization → Go-Live → Closure) in which specialized advisor agents assess project documentation at each governance gate, and human decision-makers (Portfolio Board, Steering Group) retain all Go/No-Go authority.

This is a specification-first repository. No application code exists yet — the intent is to open this repo in Claude Code (Plan Mode recommended for the first pass) and use these documents as the brief for scoping and building the system.

## Start Here

1. **[`docs/prd/PRD.md`](docs/prd/PRD.md)** — the product requirements document: problem, goals, non-goals, system overview, and links into everything else. Read this first.
2. **[`docs/decisions/DECISION-LOG.md`](docs/decisions/DECISION-LOG.md)** — every product/architecture decision made so far, with options considered and rationale. Treat this as binding unless a new entry supersedes one.
3. **[`docs/decisions/roles-and-personas.md`](docs/decisions/roles-and-personas.md)** — the 11 human roles across 4 governance tiers who use this system.
4. **[`docs/prd/agent-specifications.md`](docs/prd/agent-specifications.md)** — full behavioral specification for each of the 6 advisor agents.
5. **[`docs/prd/project-lifecycle-flow.md`](docs/prd/project-lifecycle-flow.md)** — the 6-phase lifecycle, gates, and decision criteria.
6. **[`templates/execution-templates.md`](templates/execution-templates.md)** — index into the actual Markdown templates (project idea, brief, PID, PSA, status report, go/no-go, change request, closure, etc.), each in its own file, that the agents assess against and that end users fill in.
7. **[`docs/diagrams/`](docs/diagrams/)** — visual flowchart of the lifecycle (Mermaid source + rendered HTML).

ScripeConnect12's original Dutch-language field documents (RTF/DOCX/PPTX) that this system's roles and templates were aligned against are deliberately **not** in this repo — not needed going forward, and not appropriate to publish. If a template needs to change, change `templates/execution-templates.md` and log why in the Decision Log.

## Repository Structure

```
portfolio-management-agents/
├── README.md                          ← you are here
├── CLAUDE.md                          ← guidance for Claude Code when working in this repo
├── docs/
│   ├── prd/
│   │   ├── PRD.md                     ← main product requirements document
│   │   ├── agent-specifications.md    ← behavior spec for all 6 advisor agents
│   │   └── project-lifecycle-flow.md  ← 6-phase lifecycle, gates, governance
│   ├── decisions/
│   │   ├── DECISION-LOG.md            ← all logged decisions (DEC-001 through DEC-004+)
│   │   └── roles-and-personas.md      ← 11 human roles across 4 governance tiers
│   └── diagrams/
│       ├── project_flow_diagram.mermaid
│       └── project_flow_diagram.html
└── templates/
    ├── execution-templates.md         ← index into the 11 template files below
    ├── Project Idea Submission Template.md
    ├── Project Brief Template.md
    ├── Project Initiation Document (PID) Template.md
    ├── Project Start Architecture Template.md
    ├── Project Status Report Template.md
    ├── Project Escalation Request Template.md
    ├── Go_No-Go Decision Template.md   ← "Go/No-Go" with the slash replaced (illegal in filenames)
    ├── Change Request Template.md
    ├── Project Closure Assessment Template.md
    ├── Decision Authority Matrix.md
    └── Portfolio Health Dashboard Template.md
```

## Available Skills

Skills are stored under `skill/`. Each skill has a stub at
`.claude/skills/<name>/SKILL.md` that tells Claude Code where to find the actual
skill, so Claude Code discovers them automatically when the repo is opened.

| Skill | Trigger | Location |
|-------|---------|----------|
| `idea-gate` | Assess a Project Idea `.docx` | `skill/idea-gate/` |

**Discovery:** `.claude/skills/idea-gate/SKILL.md` is a stub that tells Claude
Code to load `skill/idea-gate/SKILL.md`. No special setup required on any
platform.

To assess an idea document:
1. Open this repo in Claude Code.
2. Ask: *"Assess `<path/to/idea.docx>`"* — Claude Code will load the
   `idea-gate` skill and walk through the procedure automatically.

## Validating Changes

Run `./check` before committing — it's the single entry point for
everything that decides whether a change is good (see the
`check-convention` skill), currently the traceability check
(`check-traceability.sh`). `.github/workflows/ci.yml` runs the same
command on every PR and on pushes to `main`, plus the two network-dependent
traceability links (`check-pr-issue-link.sh`, `check-main-via-pr.sh`) —
nothing separate is invented for CI.

## Running the Evaluation

`./eval` runs the idea-gate skill headless on every `.docx` fixture,
validates each result, and reports a V1 pass rate. This is the automated
proof for KR 1.2. It is not called by CI.

```bash
# Run against all fixtures (default):
./eval

# Run a subset:
./eval --fixture "tests/fixtures/idea-v12-sample.docx"

# Repeat each fixture N times (stores every run, for V4 / KR 1.3):
./eval --runs 3
```

Results are written to `.eval-out/<timestamp>/` (git-ignored). Exit code is
0 only when every fixture validates without violations. Each fixture run
times out after 600 seconds.

`./eval` invokes `claude` with
`--allowedTools Read,Write,Bash(python skill/idea-gate/scripts/*)` —
only the tools the skill actually needs. No additional permissions are required.

**Note:** `./eval` requires the invoker's own Claude Code login — no API key
is stored in the repo. Run `chmod +x eval` after cloning if the execute bit
is not set.

## Organization data

Real organization data — your investment threshold, internal project names, calibration benchmarks, and sensitive terms — must never be committed to this repository. It lives in a local folder outside the repo.

**Folder location**

| Variable | Default |
|---|---|
| `$PMA_CONFIG_DIR` (if set) | `~/.portfolio-mgt-agents` |

Copy `config.example.yaml` from the repo root to your local config folder as `config.yaml` and fill in real values.

**Installing the pre-push hook**

```bash
bash scripts/install-hooks.sh
```

This sets `core.hooksPath` to `.githooks`. After installation, every `git push` scans added lines and filenames against `~/.portfolio-mgt-agents/denylist.txt` for any term you've listed there. If no denylist exists, the hook prints a warning and allows the push — contributors without a denylist are unblocked.

**Scanning the full tree**

```bash
python skill/idea-gate/scripts/scan_org_terms.py --all
```

Scans every tracked file (including `.docx` content) and reports any match. Exit code is 1 if anything is found. Run this before merging to `main` as a final check.

**CI gate**

A server-side scan runs on every pull request and push to `main`, inside the `check` job (the required status check). It calls:

```bash
python skill/idea-gate/scripts/scan_org_terms.py --all --locations-only --denylist-env ORG_DENYLIST
```

To activate it, the Portfolio Manager adds the denylist as a repository secret — GitHub Settings → Secrets and variables → Actions → New repository secret → name: `ORG_DENYLIST`, value: one term per line, same format as the local file.

The scan reports locations only (`<file>:<line>`) — matched terms never appear in the public log. Fork PRs do not receive the secret and therefore only warn; they will not fail the check.

## Key Constraints (do not violate without a new Decision Log entry)

- **Strictly linear governance.** No phase-skipping, no exception paths. The only flexibility mechanism is looping back to an earlier phase. (DEC-002 REVISED)
- **Humans decide, agents assess.** No agent has Go/No-Go authority in Release 1.0. (DEC-001)
- **Role descriptions are functional, not job titles.** The system must work for organizations of any size — a small org may combine several roles into one person. (DEC-003)
- **English + Markdown, role-aware, checkbox/fill-in-the-blank format** for all templates, even though the source materials from ScripeConnect12 are in Dutch and Word/PowerPoint. (DEC-004)
- **No client-identifying examples** (e.g. client-specific references present in ScripeConnect12's original source RTF) in anything we produce.

## Updating the Decision Log

If a design or scoping decision is made while working in this repo — including ones proposed by an agent and approved by a human — add a new dated entry to `docs/decisions/DECISION-LOG.md` rather than editing history. If a decision supersedes an earlier one, mark the earlier entry "Superseded by Entry N" (see Entry 2 for the pattern) rather than deleting it.

## Relationship to the Wider Decision Velocity Proposition

Decision Velocity has two building blocks operating at different cadences:

- **Portfolio Management Agents** (this repo) — the portfolio cycle.
- **Software Development Workflow Agents** (separate system, not in this repo) — the product/release/sprint/day cycle. That system is intentionally *non-linear* (looping, exception paths, phase-skipping are all permitted there), which is the opposite of this system's strictly linear model — don't import assumptions from one into the other.

Integration/handoff points between the two systems are a known, deliberately deferred gap.
