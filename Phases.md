# Phases.md — Build Roadmap

The AI should build **one phase at a time**, fully working and testable, before moving to the next. Do not start Phase 2 work while Phase 1 is incomplete.

---

## Phase 1 — Ingestion + Structural Analysis (Foundation)
**Goal:** Upload a project and get a basic structure report — no fixes yet.

- Zip upload + GitHub URL clone
- Language/framework auto-detection (start with Python + JS/TS only)
- Tree-sitter parsing pipeline for all source files
- Rules engine v1: folder-structure comparison against known-good templates
- Basic readiness score (Structure category only)
- Simple output: JSON report + minimal web page showing the score

**Done when:** uploading a messy project returns an accurate structure score and a list of specific structural issues.

---

## Phase 2 — Security & Error-Handling Checks
**Goal:** Expand the rules engine beyond structure.

- Hardcoded secret detection (API keys, tokens, passwords in source)
- `.env` usage validation
- Missing error handling detection (bare `except:`, unhandled promise rejections, etc.)
- Unused imports / dead code flags
- Readiness score expands to include Security + Error Handling categories

**Done when:** the tool reliably catches the "obvious" AI-slop patterns (hardcoded keys, empty catch blocks) on real sample projects.

---

## Phase 3 — Suggestion UI (Grammarly-Style Diff View)
**Goal:** Make findings reviewable and actionable, not just a report.

- Diff-style UI: each finding shown inline with the affected code
- Accept / reject per suggestion
- Bulk "accept all in category" option
- No auto-apply yet — this phase is about **visibility and review**, not execution

**Done when:** a user can browse every flagged issue and decide, one by one, what to fix.

---

## Phase 4 — Sandbox Runner + Verified Auto-Fix
**Goal:** Make fixes safely appliable — this is the Pinokio-inspired core.

- Isolated sandbox execution environment (Docker or scoped venv/node_modules)
- Apply accepted fixes inside the sandbox copy, not the original
- Run the app before/after each fix, confirm no breakage
- Only surface a fix as "applied" once sandbox verification passes
- If verification fails, roll back and flag the fix as "needs manual review"

**Done when:** accepted fixes are actually applied to a downloadable, restructured project, with a verified "still runs" guarantee.

---

## Phase 5 — LLM-Assisted Fuzzy Checks
**Goal:** Add the checks that can't be purely rule-based.

- Duplicated-logic detection across files (semantic, not just exact-match)
- Naming consistency review
- "This function does too much" complexity flags
- LLM calls scoped only to flagged/ambiguous regions to control cost — never blanket-scan the whole repo through the LLM

**Done when:** the tool catches issues a strict linter would miss, without excessive LLM cost per project.

---

## Phase 6 — Polish, Export, and Accounts (Later / Post-MVP)
**Goal:** Production-ready product experience.

- User accounts, saved project history
- Full "one-click production-ready" export (README, tests scaffold, `.env.example`, CI config stub)
- Optional CLI or IDE extension for live-typing suggestions (out of MVP scope, noted here for future direction)

---

### Notes for the AI
- Each phase should end with something demoable — not partial, half-wired features
- Do not jump ahead to sandboxing (Phase 4) before structural/security checks (Phases 1–2) are solid — a fix layer built on top of unreliable analysis is worse than no fix layer
- Re-read `Rules.md` before starting each new phase
