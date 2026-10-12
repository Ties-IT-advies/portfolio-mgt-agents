# CLAUDE.md — portfolio-mgt-agents

Guidance for Claude Code sessions and Hall of Automata specialists working in this repo.

## What this repo is

A specification-first repo for an agent-based portfolio governance system. Start with [`README.md`](README.md); it routes into the PRD, the Decision Log, the agent specifications and the templates. Decisions in [`docs/decisions/DECISION-LOG.md`](docs/decisions/DECISION-LOG.md) are binding unless a new entry supersedes them. Domain vocabulary (PID, PSA, DEC-XXX, Portfolio Board vs. Steering Group, governance tiers) is explained in [`CONTEXT.md`](CONTEXT.md).

## How work flows: the Hall of Automata

Development runs through the Hall of Automata (org `Ties-IT-advies`, project board #1).

- **Issues.** Work is planned as OKR → KR → Item, using the issue templates in `.github/ISSUE_TEMPLATE/`. KRs are sub-issues of an OKR, Items are sub-issues of a KR. Only Items are dispatched to a specialist (`hall:<specialist>` label). Bug fixes and investigations can be dispatched directly, without an OKR.
- **Sagas.** Initiative-sized work starts with a saga page in the [repo wiki](https://github.com/Ties-IT-advies/portfolio-mgt-agents/wiki). A dispatched Item links its open saga in its `saga:` field.
- **Branches.** Specialists work on `hall/<specialist>/issue-<N>`, branched from `main`. Nothing is committed or pushed to `main` directly.
- **Pull requests.** The PR body (not only a commit message) contains `Closes #<N>.` for the Item it delivers. GitHub only records that link from the PR title or body, and CI checks it.
- **Review and merge.** Hall PRs are reviewed by the Hall (`/hall:review`). A PR with an LGTM verdict and a green `check` may be squash-merged automatically. PRs that don't come from the Hall are merged by a human.

## CI gates

`.github/workflows/ci.yml` runs on every PR and on every push to `main`. The `check` job is a required status check: a PR can't merge until it passes.

- **`./check`** runs everything that decides whether a change is good. Today that is `check-traceability.sh`; add lint, tests and build here as they come into being, rather than as separate CI steps.
- **`check-traceability.sh`** keeps `PRD.md` and `TEST-SCENARIOS.md` consistent. Every ID heading (`F<n>`, `S<n>`) must be unique, and every token in a `**Covers:**` field must resolve to an existing heading. If you add or rename an F-ID or S-ID, update the other file in the same PR.
- **`check-pr-issue-link.sh`** fails a PR that references no issue.
- **`check-main-via-pr.sh`** flags any commit on `main` that didn't come from a PR.

Run `./check` locally before opening a PR.

## Changing templates

The execution templates in `templates/` are what the agents assess against. When a template changes, update `templates/execution-templates.md` and record why in the Decision Log.
