# dev-workplace (template)

Reusable template for the Solopreneur workflow. See `CLAUDE.md` for the project rules
(architecture is the CEO's call, Clean Code standard, etc.).

## CI/CD

The pipeline lives in `.github/workflows/ci.yml` and runs on every PR to `dev` or `main`.
It doesn't use any paid API: the AI review runs on a local model via Ollama.

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

Runs on a **self-hosted runner** (label `self-hosted`) and does the following:

1. Gets the PR's diff.
2. Checks that Ollama is available at `http://localhost:11434`.
3. Sends the diff to the local model (`qwen2.5:7b` by default) via the Ollama
   API (`POST /api/generate`).
4. Posts the response as a PR comment using the GitHub API (`gh pr comment`,
   with the `GITHUB_TOKEN` that Actions provides automatically — no need for a
   personal token).

**If Ollama isn't available** (timeout or connection refused), the job **fails
explicitly** with a `"local review unavailable, review manually"` message —
it never gives a false pass or blocks the merge silently. If the check is marked as
required in branch protection, the PR stays blocked until someone reviews it manually
or the runner/Ollama become available again.

#### Scope: a fixed risk checklist, not a bug/correctness reviewer

The prompt does **not** ask the model to find bugs or reason about whether the code is
correct. It gives it a fixed checklist of 7 low-ambiguity risk patterns to scan the diff
for, and nothing else:

1. Hardcoded secrets, API keys, tokens, or passwords in code or config
2. SQL queries built via string concatenation/formatting instead of parameterized queries
3. Bare `except:` clauses or empty exception handlers that silently swallow errors
4. User input passed directly to `eval()`, `exec()`, `os.system()`, or shell commands
   without sanitization
5. Missing input validation on function parameters that are later used in file paths,
   DB queries, or system calls
6. Debug code left in (print statements, `console.log`, commented-out blocks,
   `TODO`/`FIXME`/`XXX` markers)
7. Obvious resource leaks (files/connections opened without being closed or without a
   context manager)

For each item it must answer "Not found" or cite the exact line/snippet — no free-form
suggestions, no docstring/style/test commentary. If none of the 7 apply, the whole review
is just `"No matches found in this diff."`

This scope is intentional, based on real testing: we ran `phi4-mini` (3.8B, the current
default) against a diff containing a genuine but subtle business-logic bug (a tier-boundary
off-by-one — `>` used instead of `>=`) with an earlier, open-ended "find bugs, give
Input/Expected/Actual" prompt. Across two prompt iterations, the model never reliably
caught it — it either invented a bug that wasn't actually there, or, once the prompt
demanded rigor, went silent and reported nothing rather than risk being wrong. A 3.8B
local model isn't a substitute for reasoning about correctness; it can reliably
pattern-match a short list of known-bad shapes, so that's what this job asks it to do.
**Business-logic bugs — off-by-one errors, wrong boundary conditions, incorrect
calculations, wrong conditionals, and similar — are explicitly out of scope for
`local-review` and it will not catch them. That's expected, not a defect in this job's
configuration.** Those need `/solopreneur:review` or a human reviewer.

#### Changing the Ollama model

Pull the model on the runner machine and update `env.OLLAMA_MODEL` in
`.github/workflows/ci.yml`:

```bash
ollama pull llama3.1:8b   # or whichever model you want to use
```

```yaml
# .github/workflows/ci.yml, local-review job
env:
  OLLAMA_MODEL: llama3.1:8b
```

### 3. `/solopreneur:review` — manual review, not automatic

`/solopreneur:review` (from the Solopreneur plugin) does **not** run in the pipeline. It
remains available for the CEO to invoke manually for everything `local-review`'s fixed
checklist doesn't cover — in practice, that means all business-logic and correctness
review, since a small local model isn't reliable at that kind of open-ended reasoning
(see "Scope" above).

## Self-hosted runner on the Arch/CachyOS machine

The `local-review` job needs a runner registered with the `self-hosted` label on this
machine (where Ollama runs). Actual steps to register it (replace `<TOKEN>` with the
value given by the `gh api` command):

```bash
# 1. Create a folder for the runner and enter it
mkdir -p ~/actions-runner && cd ~/actions-runner

# 2. Download the runner package (check the latest version at
#    https://github.com/actions/runner/releases and adjust the URL/version)
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64-<VERSION>.tar.gz
tar xzf actions-runner-linux-x64.tar.gz

# 3. Request a registration token for this repo with gh (already authenticated with `gh auth login`)
TOKEN=$(gh api -X POST repos/yeahtosty/dev-workplace/actions/runners/registration-token --jq .token)

# 4. Configure the runner with that token and the "self-hosted" label
./config.sh --url https://github.com/yeahtosty/dev-workplace --token "$TOKEN" --labels self-hosted

# 5a. Run it in the foreground (to test)
./run.sh

# 5b. Or install it as a systemd service so it keeps running
sudo ./svc.sh install
sudo ./svc.sh start
```

Alternative without `gh api`: go to **Settings → Actions → Runners → New self-hosted runner**
on `https://github.com/yeahtosty/dev-workplace`, which shows the same commands with the
token already generated.

Prerequisite on this machine: Ollama running and reachable at `localhost:11434`, with
the default model already pulled:

```bash
ollama pull qwen2.5:7b
```

## Adjusting the conditional review thresholds

| What to adjust | Where |
|---|---|
| Changed-lines threshold (default: 80) | `env.DIFF_LINE_THRESHOLD` in `.github/workflows/ci.yml` |
| Sensitive folders/paths | `.github/sensitive-paths.txt` (one path per line, works as a prefix) |
| Ollama model (default: `qwen2.5:7b`) | `env.OLLAMA_MODEL` in the `local-review` job in `.github/workflows/ci.yml` |
