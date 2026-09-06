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

## CI/CD and conditional review (no paid APIs)

The pipeline lives in `.github/workflows/ci.yml` and doesn't use any paid API (no OpenAI,
no Claude API, etc.). Summary of the flow — full detail is in `README.md`:

- On **every PR to `dev` or `main`**, the `checks` job runs: lint and unit tests
  (today they're generic placeholders because the real stack hasn't been decided yet —
  see the comments in `ci.yml` to replace them with the real linter/tests per language)
  and the diff-size calculation + sensitive-folder detection.
- If the diff exceeds **80 changed lines** (`env.DIFF_LINE_THRESHOLD` in `ci.yml`) **or**
  touches a path listed in `.github/sensitive-paths.txt`, the `local-review` job
  triggers. Both thresholds are adjustable — the line count is changed in
  `ci.yml`, the sensitive paths are added/removed in `.github/sensitive-paths.txt`,
  without touching the workflow.
- `local-review` runs on a **self-hosted runner** (label `self-hosted`) on the CEO's
  CachyOS/Arch machine, where Ollama lives (`localhost:11434`, model `qwen2.5:7b` by
  default — change it in `env.OLLAMA_MODEL` inside `ci.yml`, after pulling it with
  `ollama pull <model>`). If Ollama doesn't respond, the job **fails explicitly** with a
  "local review unavailable, review manually" message — it never gives a false pass or
  blocks silently.
- **`/solopreneur:review` is not part of the automatic pipeline.** It remains a manual
  review on demand, requested by the CEO, for cases the local reviewer (a 7B model
  running locally) doesn't cover well — typically complex business logic that needs
  more reasoning than a small model can provide.
- How to register the self-hosted runner on the Arch machine: see the
  "CI/CD — self-hosted runner" section of `README.md`.
