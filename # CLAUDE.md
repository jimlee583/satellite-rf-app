# CLAUDE.md — satellite-rf-app

You are Claude Code operating inside the `satellite-rf-app` repository.
Follow these rules strictly.

## 0) Prime directive
Make small, reviewable changes that preserve existing behavior unless explicitly asked.
If something is ambiguous, make the simplest reasonable assumption and state it briefly.

## 1) Repo context & boundaries
- This repo likely contains:
  - a Python/FastAPI backend (API endpoints, link-budget math, validation)
  - a React/TypeScript frontend (Vite, UI controls, plots)
  - optional Docker/Docker Compose for local dev
- Do not introduce new frameworks, UI libraries, or big structural reorganizations unless I ask.
- Do not modify unrelated files “for cleanup.”

## 2) Safety rules for commands
### Read-only commands you may run without asking
- `pwd`, `ls`, `cat`, `rg`, `find`
- `git status`, `git diff`, `git log --oneline -n 20`
- `python --version`, `node --version`
- Test/lint commands that do NOT change files:
  - `pytest` / `python -m pytest`
  - `ruff check .`
  - `mypy .` (if configured)
  - `npm test`, `npm run build`, `npm run typecheck`, `npm run lint` (if present)

### Commands you must ask before running
- Anything that installs/updates deps or lockfiles:
  - `pip install`, `uv sync`, `npm install`, `npm audit fix`, etc.
- Anything that alters infra:
  - `docker build`, `docker compose up`, `gcloud`, CI/CD edits
- Anything destructive or history-rewriting:
  - `rm -rf`, `git reset`, `git rebase`, `git push --force`

If a command might take a long time (builds, docker), ask first.

## 3) Git workflow
- Use a feature branch unless I explicitly say to work on `main`.
  - Branch naming: `feature/<short>`, `fix/<short>`, `chore/<short>`
- Never force-push.
- Keep commits focused and readable.
  - Commit messages: imperative present tense (“Add…”, “Fix…”, “Refactor…”)
- Before committing:
  - run relevant tests/linters for the touched area (backend/frontend)

## 4) Backend (Python / FastAPI) rules
- Preserve the API contract (paths, response shapes) unless asked to change it.
- Use type hints and Pydantic models for request/response schemas.
- Keep pure math/link-budget logic separate from API handlers when possible.
- Avoid hidden behavior changes:
  - If you change a formula, cite where it lives and add a quick note in the PR summary.

### Backend testing expectations
- Add/adjust `pytest` tests for any behavior change or bug fix.
- Prefer deterministic tests (no network, no time dependence).
- If there’s a `tests/` folder, follow its conventions.

## 5) Frontend (React / TypeScript / Vite) rules
- Keep UI consistent with existing components and styling.
- Prefer strict types; avoid `any` unless unavoidable.
- Do not add new UI libs unless asked.
- Any new calculation inputs must:
  - validate user input (range/type)
  - display units clearly (GHz, dBW, dBK, deg, km, etc.)
  - be wired end-to-end (UI → API request → response → UI)

## 6) Link budget / RF math rules (important)
- Don’t change math silently. If updating:
  - show the old vs new equation in a short note
  - add a test with a known numeric case
- Keep consistent units:
  - dBW / dBm, dB, dBi, dBK, K, Hz, GHz, degrees/radians
- If conversions are involved, be explicit about:
  - `10*log10()` vs `20*log10()`
  - bandwidth usage (Hz)
  - when to add/subtract implementation margin, scan loss, etc.
- If you’re unsure which convention the repo uses, search first and follow existing patterns.

## 7) Dependencies
- Do not add or upgrade dependencies unless I explicitly request it.
- If a dependency is truly necessary, ask first and explain why.
- Avoid touching lockfiles unless required.

## 8) Documentation
If you add an endpoint, UI feature, or a new preset:
- Update README or relevant docs (short and practical)
- Include a quick usage example (curl or a UI note)

## 9) How to communicate changes (required)
Before making edits, provide:
- A short plan (3–7 bullets)
- Which files you will touch
- Any commands you want to run (ask first if needed)

After edits, provide:
- Summary of what changed
- How to test (exact commands)
- Any assumptions or tradeoffs

## 10) Stop & ask if
- You need to modify Docker/Compose, CI, or cloud deploy files
- You need to add/upgrade dependencies
- You encounter failing tests and the root cause isn’t obvious
- The change could break API compatibility or existing UI flows
