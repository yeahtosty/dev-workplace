# dev-workplace (template)

Reusable template for the Solopreneur workflow. See `CLAUDE.md` for the project rules
(architecture is the CEO's call, Clean Code standard, etc.).

## CI/CD

The pipeline lives in `.github/workflows/ci.yml` and runs on every PR to `dev` or `main`.
It doesn't use any paid API, and as of this version, no AI model at all: `local-review` is
a deterministic pattern scan (see below).

### 1. `checks` job (always runs)

- **Lint** and **unit tests**: today they're placeholders (`echo "TODO..."`) because this
  repo is a template and the real stack hasn't been decided yet. Once it is, replace
  those two steps in `ci.yml` — right there are comments with examples for
  Python, Node/TS, Go, and Rust.
- **Diff analysis**: counts changed lines (insertions + deletions) against the
  PR's base and checks whether any modified file starts with one of the paths
  listed in `.github/sensitive-paths.txt`.

### 2. `local-review` job (conditional)

Triggers only if:

- the diff changes more than **80 lines** (adjustable in `env.DIFF_LINE_THRESHOLD` inside
  `.github/workflows/ci.yml`), **or**
- it touches a folder listed in `.github/sensitive-paths.txt` (by default: `auth/`,
  `payments/`, `security/`, `migrations/` — adjustable by editing that file, one path per
  line).

Runs on a **GitHub-hosted runner** (`ubuntu-latest`, same as `checks` — no self-hosted
runner needed for this job) and does the following:

1. Gets the PR's diff.
2. Runs `.github/scripts/local_review_scan.py` against it.
3. Posts the output as a PR comment using the GitHub API (`gh pr comment`,
   with the `GITHUB_TOKEN` that Actions provides automatically — no need for a
   personal token).

#### Scope: a deterministic pattern scan, not an AI reviewer

`local_review_scan.py` does **not** call any model. It parses the diff's added lines
(lines starting with `+`, excluding the `+++` file header) and regex-matches each one
against 6 fixed, low-ambiguity risk patterns:

1. Hardcoded secrets, API keys, tokens, or passwords in code or config
2. SQL built via string concatenation/f-strings/`.format()` instead of parameterized queries
3. Bare `except:` clauses, or empty except/catch blocks (Python and JS/TS)
4. `eval()`, `exec()`, `os.system()`, or `subprocess(..., shell=True)`
5. Debug leftovers added in the diff: `print(`, `console.log(`, `debugger;`,
   `TODO`/`FIXME`/`XXX`
6. `open()` without a context manager — flagged as a **heuristic warning**, not a hard
   finding, since this one has real false-positive risk

Every match cites the actual `file:line` and the actual line content from the diff —
there's no summarization step, so there's nothing to hallucinate. If none of the 6 apply,
the whole comment is just `"No matches found in this diff."`

**This replaced an earlier Ollama/phi4-mini-based version of this job**, based on real
testing: we ran `phi4-mini` (3.8B, local) against a diff with a genuine but subtle
business-logic bug (a tier-boundary off-by-one, `>` used instead of `>=`) across three
prompt iterations — open-ended "find bugs, give Input/Expected/Actual", and finally a
fixed 7-item checklist nearly identical to the one above. Every version either invented a
finding that wasn't actually in the diff, or produced broken/self-contradictory output —
including, on the checklist version, citing the checklist item's own description back as
if it were a quoted line from the code. A 3.8B local model was not reliable even for
closed-set pattern-matching against a diff it had directly in front of it, so this job
stopped calling a model entirely and does the matching with real regexes instead.

**This is still not a correctness or business-logic reviewer.** Business-logic bugs —
off-by-one errors, wrong boundary conditions, incorrect calculations, wrong conditionals,
and similar — are explicitly out of scope for `local-review` and it will not catch them.
That's expected, not a defect. Those need `/solopreneur:review` or a human reviewer.

#### Future option: local LLM review, if revisited later

If local LLM-based review is worth trying again in the future, it would need a
meaningfully larger model — 24GB+ VRAM class — than the hardware this template was
developed on supports. The Ollama-based approach here was tested across three prompt
iterations and abandoned because a small (3.8B) local model isn't reliable at this task,
not for lack of prompt-engineering effort. This isn't something to implement now; it's a
note for whoever revisits this with better hardware available.

### 3. `/solopreneur:review` — manual review, not automatic

`/solopreneur:review` (from the Solopreneur plugin) does **not** run in the pipeline. It
remains available for the CEO to invoke manually for everything `local-review`'s fixed
pattern scan doesn't cover — in practice, that means all business logic, architecture,
and security judgment beyond pattern-matching, since none of that can be done with regex.

## Adjusting the conditional review thresholds

| What to adjust | Where |
|---|---|
| Changed-lines threshold (default: 80) | `env.DIFF_LINE_THRESHOLD` in `.github/workflows/ci.yml` |
| Sensitive folders/paths | `.github/sensitive-paths.txt` (one path per line, works as a prefix) |
| Pattern checks | `.github/scripts/local_review_scan.py` (edit the `CHECKS` list) |
