# Instructions for AI coding agents working on WardPulse

WardPulse is a hackathon project: an AI early warning system for patient deterioration in understaffed hospital wards. It tells a nurse the top 2 actions for the next 15 minutes.

## Read first, in this order

1. `docs/PROJECT_CONTEXT.md` (what and why, decisions, rules)
2. `docs/contracts.md` and `backend/shared/schemas.py` (exact data shapes and behaviour)
3. `docs/PROGRESS.md` (what is done, what is next, blockers)

## Rules

- Work only inside the folder your task names. Do not refactor other modules.
- Do not edit `backend/shared/schemas.py` or `docs/contracts.md` unless the task says so. If a contract looks wrong, write the problem under "Open questions" in `docs/PROGRESS.md` and continue with the closest reasonable behaviour.
- The engine is pure logic: no web, database, file or clock access. Time is passed in as `now`.
- Run Python from the `backend/` directory. Import shapes with `from shared.schemas import ...`.
- Cards come from the closed set in `schemas.py`. No LLM output, no drug advice.
- Any vital can be `None`.
- No real patient data. Never commit `.env`, `venv/`, `node_modules/`, `*.db`, `data/raw/`.
- Write tests for what you build and run them before finishing.

## When you finish a task (always, every time)

1. Run the tests and the relevant program. Do not claim success without running them.
2. Update `docs/PROGRESS.md`:
   - set your package's status in the table (DONE, IN PROGRESS or BLOCKED) and fill Owner and Notes,
   - tick any contract tests that now pass,
   - add a line at the TOP of the Change log: date, package, what you built, files touched, test result (exact pass/fail counts), problems or shortcuts, and what should happen next,
   - update the "Next recommended prompt" line near the top of the file.
   A different AI (a new Claude chat) will read this file to decide the next prompt, so be precise and honest, including failures.
3. Commit in small logical commits with a prefix: `contract:` `engine:` `sim:` `eval:` `ml:` `api:` `ui:` `docs:` `chore:`. Run `git status` and `git diff` first so no stray files are committed.
4. `git pull --rebase`, then `git push` to GitHub. If the push fails, say so clearly in your final message and in PROGRESS.md. If git pull or git push does not finish within 60 seconds, or asks for credentials, stop immediately. Do not retry or wait. Tell the human 'push is stuck, please push manually from PowerShell' and continue with the next task.
5. End your final message with: what you did, test results, anything the human must do, and the next prompt ID.
