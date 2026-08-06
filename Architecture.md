# Architecture.md

## 1. High-Level Flow

```
User Input (zip / GitHub URL / paste)
        │
        ▼
┌──────────────────┐
│  Ingestion Layer  │  clone/unzip, detect language & framework
└──────────────────┘
        │
        ▼
┌──────────────────┐
│   Parsing Layer   │  Tree-sitter → AST per file
└──────────────────┘
        │
        ▼
┌──────────────────────────┐
│      Analysis Engine      │
│  ┌──────────┐ ┌─────────┐ │
│  │  Rules   │ │   LLM   │ │   deterministic checks (structure,
│  │  Engine  │ │  Layer  │ │   secrets, imports) + LLM-assisted
│  └──────────┘ └─────────┘ │   checks (naming, duplication, intent)
└──────────────────────────┘
        │
        ▼
┌──────────────────┐
│ Suggestion Layer  │  generates diffs, one suggestion per issue
└──────────────────┘
        │
        ▼
┌──────────────────────────┐
│   Sandbox Runner (Pinokio- │  isolated venv/container, applies fix,
│   inspired isolation)      │  runs app, confirms no breakage
└──────────────────────────┘
        │
        ▼
┌──────────────────┐
│   Output Layer    │  restructured project, readiness report, diff view
└──────────────────┘
```

## 2. Layer Responsibilities

| Layer | Responsibility | Key Tech |
|---|---|---|
| Ingestion | Accept zip/GitHub URL/paste, detect language & framework | GitPython, simple file-type detection |
| Parsing | Convert each source file into an AST for structural analysis | Tree-sitter (multi-language) |
| Analysis — Rules Engine | Deterministic checks: folder layout vs. template, hardcoded secrets, missing `.env`, unused imports | Custom rule set (regex + AST pattern matching) |
| Analysis — LLM Layer | Fuzzy checks: naming consistency, duplicated logic, "does this function do too much" | LLM API (Claude/GPT) via structured prompts, used sparingly for cost control |
| Suggestion Layer | Converts findings into individual, reviewable diffs | Custom diff generator |
| Sandbox Runner | Isolated execution environment to test the app before/after a fix is applied — **this is the Pinokio-inspired piece**: every install, every run, is boxed off from the host system | Docker (or a lightweight venv/node_modules jail, Pinokio-style, for local-first execution without full container overhead) |
| Output | Final restructured project + readiness report (score + category breakdown) | Static file generation, JSON report |

## 3. Why the Sandbox Layer Matters (Pinokio-Inspired)

Applying automated fixes to someone's code is risky — an "improvement" that breaks the app is worse than doing nothing. Borrowing directly from Pinokio's isolation model:

- Every fix is applied inside an **isolated copy** of the project, never the user's original files directly
- Dependencies, venvs, and runtime binaries needed to *test* a fix are installed into a scoped, disposable directory — never touching the host system
- The app is run **before** and **after** each fix to confirm it still boots
- Only after verification does the fix get proposed to the user as "safe to apply"

This keeps the tool trustworthy: users can accept fixes without worrying CodePolish just silently broke their app.

## 4. Repository / Folder Structure (for CodePolish itself)

```
codepolish/
├── backend/
│   ├── ingestion/          # zip/repo intake, language detection
│   ├── parsing/            # tree-sitter wrappers per language
│   ├── analysis/
│   │   ├── rules/          # deterministic rule definitions
│   │   └── llm/            # LLM prompt templates + client
│   ├── sandbox/            # isolated runner, Pinokio-style execution
│   ├── suggestions/        # diff generation, scoring logic
│   └── api/                # FastAPI routes
├── frontend/
│   ├── src/
│   │   ├── components/     # diff viewer, score dashboard, upload UI
│   │   ├── pages/
│   │   └── lib/            # API client
│   └── public/
├── templates/               # known-good folder layouts per framework
├── tests/
└── docs/
    ├── PRD.md
    ├── Architecture.md
    ├── Rules.md
    ├── Phases.md
    ├── Design.md
    └── Memory.md            # added once coding begins
```

## 5. Suggested Tech Stack

| Area | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | React + Tailwind |
| Parsing | Tree-sitter |
| Sandbox / Isolation | Docker (or lightweight scoped venv/node_modules, Pinokio-style) |
| LLM Integration | Claude/GPT API, called only for fuzzy checks to control cost |
| Storage (project sessions) | PostgreSQL (metadata) + local/blob storage (uploaded projects) |
| Diff Rendering | `diff-match-patch` or similar, rendered in-browser |

## 6. Data Flow Summary

1. User uploads → stored in a scoped temp directory (one per session)
2. Parser walks the project, builds an AST per file
3. Rules engine runs first (cheap, deterministic) → structural + security findings
4. LLM layer runs second, only on flagged or ambiguous areas (cost control)
5. All findings become a unified list of suggestions with severity + category
6. User reviews suggestions in the diff UI, accepts/rejects individually or in bulk
7. Accepted fixes are applied in the sandbox, app is re-run to verify
8. Verified project is packaged as the final output, alongside the readiness report
