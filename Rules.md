# Rules.md — AI Boundaries for Building This Project

These rules govern how an AI coding assistant (Claude Code, Cursor, etc.) should behave while building CodePolish. Paste this file into the assistant's context at the start of every session.

## 1. Libraries & Tools — Use / Avoid

**Use:**
- Tree-sitter for all AST parsing — never hand-rolled regex parsing for code structure
- FastAPI for the backend API — not Flask, not Django (keep it lightweight and async-friendly)
- Docker (or an explicitly scoped subprocess/venv jail) for sandboxing — **never** run untrusted or user-uploaded code directly on the host process
- `python-dotenv` / `.env` for all secrets — never hardcode API keys, ever, including in example code or tests

**Avoid:**
- No `eval()` or `exec()` on user-uploaded code, under any circumstance
- No shelling out to arbitrary user-supplied commands without sandboxing
- No third-party LLM calls on raw user code without an explicit opt-in step (privacy)
- No heavyweight ORMs for the MVP — raw SQL or a lightweight query builder is fine for the metadata DB

## 2. Error Handling

- Every sandboxed execution **must** fail loudly and visibly to the user — never silently swallow an error from a fix that broke the app
- Every API endpoint returns structured error responses (`{ "error": { "code", "message" } }`), never a raw stack trace to the client
- Any exception during rule-engine or LLM analysis should degrade gracefully — skip that one check and continue, don't crash the whole analysis run
- Log all sandbox failures with enough context to reproduce, but never log secrets or `.env` contents

## 3. Security Boundaries

- User-uploaded code is **never** trusted — always executed inside the isolated sandbox layer, never on the host
- No outbound network access from within the sandbox unless explicitly required by the project being analyzed (and even then, sandboxed/mocked where feasible)
- Uploaded projects are stored in per-session scoped directories and deleted after a defined retention window — never persisted indefinitely without consent
- Any detected hardcoded secret in a user's uploaded code must be flagged, **not** logged or transmitted anywhere (including to the LLM layer) — redact before sending analysis context to an LLM

## 4. Scope Boundaries — What the AI Should and Shouldn't Do

**Should:**
- Fix structure, security basics, error handling, naming consistency, duplication
- Explain every suggested fix in plain language before applying it
- Ask for confirmation before any bulk "fix everything" action
- Keep fixes minimal and targeted — one concern per suggested diff

**Should NOT:**
- Rewrite or "improve" business logic / functional behavior — that's out of scope and risks breaking intent
- Silently change public API signatures, database schemas, or function contracts without flagging it explicitly
- Auto-apply any fix without it passing sandbox verification first
- Guess at intent when code is ambiguous — flag it as a question for the user instead of assuming

## 5. Style & Conventions

- Python: PEP8, type hints required on all new functions
- JavaScript/TypeScript: Airbnb style guide baseline, TypeScript preferred over plain JS for new code
- Every new module gets a short docstring/comment block explaining its responsibility
- Commit-sized changes — don't bundle unrelated fixes into a single diff/PR
