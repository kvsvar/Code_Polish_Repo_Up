# PRD.md — Project Requirements Document

## Project Name
**CodePolish** *(working title — swap freely; alternatives: Structura, RefactorLens, VibeCheck)*

## One-Line Pitch
Grammarly for code — upload or paste a "vibe-coded" project and get it automatically checked, corrected, and restructured into an industry-standard, production-ready codebase.

---

## 1. The Problem

AI coding tools (Claude, ChatGPT, Cursor, Copilot) make it trivially easy to generate working code fast — but "working" and "production-ready" are not the same thing. Code produced this way ("vibe coding") typically has:

- No consistent folder/file structure (everything dumped in one file or one flat folder)
- Missing or inconsistent error handling
- Hardcoded secrets, no `.env` usage
- No input validation or security basics
- Inconsistent naming conventions
- No tests, no README, no dependency pinning
- Copy-pasted or duplicated logic across files
- No separation of concerns (UI, logic, and data access all mixed together)

Most people using AI to code — students, hobbyists, indie hackers, non-CS-background builders — don't know what "industry-ready" looks like, so they don't know what to ask the AI to fix. There's no tool that inspects the *actual generated codebase* and tells them, concretely, what's wrong and fixes it — the way Grammarly does for prose.

## 2. The Solution

A tool that takes a codebase (via upload, GitHub URL, or paste) and:

1. **Analyzes** it against a rules engine + LLM-assisted checks (structure, security, style, error handling, duplication)
2. **Scores** it on a "production-readiness" scale, broken down by category
3. **Suggests fixes** inline, Grammarly-style — this file should live here, this function has no error handling, this secret should be in `.env`
4. **Applies fixes** on request — either one at a time or "fix everything," restructuring the project into a standard, recognized layout for its stack
5. **Verifies** that applied fixes didn't break the app, by running it in an isolated local sandbox before/after (inspired by Pinokio's isolated execution model) and diffing behavior

## 3. Target Users

| User | Need |
|---|---|
| Students / bootcamp learners | Understand what "good structure" actually looks like, not just get an A |
| Indie hackers / solo builders | Ship an AI-generated MVP without embarrassing security holes or unmaintainable spaghetti |
| Non-CS-background builders ("vibe coders") | A safety net that catches what they don't know to look for |
| Small teams onboarding AI-generated code | A pre-merge gate that flags AI-slop before it enters the main branch |

## 4. Core Features (MVP scope)

- **Ingestion**: upload a `.zip`, paste a GitHub repo URL, or paste code directly
- **Structure Analysis**: detect language/framework, compare folder layout against known-good templates (e.g., standard Next.js layout, standard Flask layout)
- **Code Quality Checks**: missing error handling, hardcoded secrets, unused imports, duplicated logic, missing input validation
- **Readiness Score**: single 0–100 score plus a breakdown by category (Structure, Security, Error Handling, Style, Documentation)
- **Inline Suggestions**: Grammarly-style annotated diff view — click to accept/reject each suggestion
- **One-Click Restructure**: auto-generate a properly organized project (correct folders, `.env.example`, `README.md`, basic tests scaffold) from the messy input
- **Sandbox Verification**: before finalizing a fix, run the app in an isolated environment to confirm it still boots/runs

## 5. Explicit Non-Goals (for MVP)

- Not a full CI/CD pipeline
- Not a general-purpose linter replacement (we build on top of existing linters, not compete with ESLint/Pylint)
- Not attempting to fix business logic or functional bugs — only structure, safety, and maintainability
- Not supporting every language at launch — start with **Python** and **JavaScript/TypeScript**, expand later
- Not a real-time IDE plugin at MVP stage — that's a later phase

## 6. Success Metrics

- A messy uploaded project reliably produces a higher, explainable readiness score after fixes are applied
- Sandbox verification confirms the app still runs after restructuring (zero regressions from applied fixes)
- Time from "upload" to "restructured, runnable project" under a few minutes for small-to-medium projects
