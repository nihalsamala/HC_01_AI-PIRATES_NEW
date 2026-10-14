# Taking over as a new Claude chat

## What the human pastes into a new Claude chat

1. The text below.
2. The full contents of `docs/PROGRESS.md` and `docs/PROJECT_CONTEXT.md` (and `docs/contracts.md` if asked).

```
You are taking over as technical lead for a hackathon project called WardPulse (healthcare PS1: AI early warning for patient deterioration in understaffed wards). The build is done by Antigravity coding agents that I run by pasting prompts. I have very little time left (about 24 hours total from 14 Oct 2026), so be fast and concise.
Below are PROGRESS.md and PROJECT_CONTEXT.md from my repo. Do this:
1. In 3 lines tell me where the project stands and the biggest risk.
2. Give me the NEXT prompt(s) to paste into Antigravity, as short launcher lines, in code blocks. Parallel lanes are allowed (see AGENT_PROMPTS.md lanes).
3. If I paste an agent's final message or an error, give me a targeted fix prompt.
I am not a healthcare expert: explain medical terms simply. Be honest about weaknesses.
```

## Launcher prompts for Antigravity (one per package)

Replace PX with the package id (P0 to P9). Each agent reads the repo files itself.

```
Read AGENTS.md first. Then open docs/AGENT_PROMPTS.md and carry out ONLY the prompt block under the heading for PX, exactly as written, including its "Finish" steps (tests, update docs/PROGRESS.md, small commits, git pull --rebase, git push to GitHub). When done, tell me the test results and the next prompt id.
```

Ready lines:
- P0: `...the heading "P0 Bootstrap"...`
- P1: `...the heading "P1 Simulator"...`
- P2: `...the heading "P2 Engine A"...`
- P3: `...the heading "P3 Engine B"...`
- P4: `...the heading "P4 Backend"...`
- P5: `...the heading "P5 Frontend"...`
- P6: `...the heading "P6 Integration"...`
- P7: `...the heading "P7 Evaluation"...`
- P8: `...the heading "P8 LightGBM"...`
- P9: `...the heading "P9 Polish"...`

## Bug-fix launcher (for any failure)

```
Read AGENTS.md and docs/PROGRESS.md. Problem: <paste the error or what is wrong>. Find the root cause, fix it in the module that owns the bug with the smallest change, add or update a test that would have caught it, run the full test suite, update docs/PROGRESS.md (Change log at the top), commit with the right prefix, git pull --rebase, git push, and tell me what you changed.
```
