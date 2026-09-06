# CLAUDE.md — dev-workplace (template)

This repository is a **reusable template** for bootstrapping new projects with the
Solopreneur workflow. It is not a product and has no end users — it's the configuration
base (`CLAUDE.md`, agents, and skills) that gets copied or inherited when starting a real
project.

## Non-negotiable rule: architecture is the human's call

**No agent proposes, decides, or changes the project's architecture without explicit
approval from the CEO (the human).** This rule applies to any agent or skill run from
this template, in any project derived from it, and takes priority over any "work
autonomously" instruction — autonomy does not include deciding architecture.

- An agent can **analyze and present** architecture options (trade-offs, risks,
  alternatives), but cannot **choose** one or start implementing it as if it were already
  decided.
- The following count as architecture decisions: choosing a stack or framework, defining
  folder/module structure, choosing a database or data model, defining API contracts,
  choosing a deployment/infrastructure strategy, or any decision that's costly to revert
  once code is built on top of it.
- If a task requires this kind of decision and it hasn't already been made by the CEO,
  the agent must **stop and ask** (e.g. with `AskUserQuestion`) instead of assuming a
  "reasonable" option and moving forward.

## Code quality standard: Clean Code

This template incorporates the rules from
[clean-code-skills](https://github.com/ertugrul-dmr/clean-code-skills) (Robert C. Martin,
*Clean Code*, ch. 17) for Python and TypeScript as the default standard:

- `.claude/skills/python/` and `.claude/skills/typescript/` contain the 7 original
  skills per language (`boy-scout`, `python-clean-code` / `typescript-clean-code`,
  `clean-names`, `clean-functions`, `clean-comments`, `clean-general`, `clean-tests`),
  copied in full from the original repo (MIT license — see
  `.claude/skills/THIRD_PARTY_NOTICES.md`).
- The `engineer` agent (`.claude/agents/engineer.md`) preloads `python-clean-code` and
  `typescript-clean-code` as the standard reference for any coding task; the rest of the
  skills (`clean-names`, `clean-functions`, `boy-scout`, etc.) trigger automatically
  based on the task context.
- The `conventions` skill (`.claude/skills/conventions/SKILL.md`) documents this as part
  of the team's shared conventions.

## Using this template

When starting a real project from this template: copy this `CLAUDE.md` and the
`.claude/` folder to the new repo, and adjust only the product-specific content
(name, stack if already decided, etc.) — the two rules above remain unchanged.

## CI/CD and conditional review (no paid APIs, no local LLM)

The pipeline lives in `.github/workflows/ci.yml` and doesn't use any paid API (no OpenAI,
no Claude API, etc.) — and, as of this version, no AI model of any kind. Summary of the
flow — full detail is in `README.md`:

- On **every PR to `dev` or `main`**, the `checks` job runs: lint and unit tests
  (today they're generic placeholders because the real stack hasn't been decided yet —
  see the comments in `ci.yml` to replace them with the real linter/tests per language)
  and the diff-size calculation + sensitive-folder detection.
- If the diff exceeds **80 changed lines** (`env.DIFF_LINE_THRESHOLD` in `ci.yml`) **or**
  touches a path listed in `.github/sensitive-paths.txt`, the `local-review` job
  triggers. Both thresholds are adjustable — the line count is changed in
  `ci.yml`, the sensitive paths are added/removed in `.github/sensitive-paths.txt`,
  without touching the workflow.
- **`local-review` is a deterministic pattern scanner, not an AI reviewer.**
  `.github/scripts/local_review_scan.py` regex-scans the diff's added lines for 6 fixed
  risk patterns — hardcoded secrets/API keys/tokens, SQL built via string
  concatenation/f-strings/`.format()`, bare `except:`/empty except-or-catch blocks,
  `eval`/`exec`/`os.system`/`subprocess(..., shell=True)`, leftover debug code
  (`print`/`console.log`/`debugger;`/`TODO`/`FIXME`/`XXX`), and `open()` without a
  context manager (flagged as a heuristic warning — this one has real false-positive
  risk). Pure text matching against the actual diff content, with real file:line
  citations — nothing to hallucinate, nothing that requires judgment. If none of the 6
  apply, the PR comment is just `"No matches found in this diff."` It runs on a
  GitHub-hosted runner, same as `checks` — **no self-hosted runner or Ollama needed for
  this job anymore.**
  - **This replaces an earlier Ollama/phi4-mini-based version of this job.** Three real
    tests against `phi4-mini` (3.8B, local) — open-ended bug-hunting, a strict
    Input/Expected/Actual requirement, and a fixed 7-item checklist — each either
    hallucinated a finding that wasn't in the diff or produced broken/contradictory
    output, even on a closed, low-ambiguity checklist it only had to pattern-match
    against. A 3.8B local model isn't reliable even for that, so this job stopped
    calling a model at all. See the "Future option: local LLM review" note in
    `README.md` if this is revisited with better hardware.
  - **This is not a correctness or business-logic reviewer**, same as before it became
    deterministic: it only catches the 6 fixed patterns above. Business-logic bugs
    (off-by-one errors, wrong boundary conditions, incorrect calculations, wrong
    conditionals, etc.) and anything needing actual reasoning are explicitly out of
    scope — it will not catch them, and that is expected, not a defect.
- **`/solopreneur:review` is not part of the automatic pipeline.** It remains a manual
  review on demand, requested by the CEO, for everything `local-review`'s fixed pattern
  scan doesn't cover — in practice, all business logic, architecture, and security
  judgment beyond pattern-matching.
