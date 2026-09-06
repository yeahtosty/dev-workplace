#!/usr/bin/env python3
"""Deterministic pattern scan for the local-review CI job.

Scans only the added lines of a unified diff for a fixed set of low-ambiguity
risk patterns. No model call, nothing that can hallucinate — pure regex text
matching against the actual diff content, with real file:line references.
"""

import fnmatch
import re
import sys

# The scanner's own source and the docs describing it legitimately contain the
# exact strings these checks look for (regex literals like r"\beval\s*\(",
# prose mentioning TODO/FIXME, example snippets) — exclude that infrastructure
# from all checks rather than trying to special-case each pattern around it.
EXCLUDED_PATH_PATTERNS = [
    ".github/scripts/*",
    "*.md",
    ".github/workflows/*.yml",
]


def is_excluded_path(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in EXCLUDED_PATH_PATTERNS)


def make_regex_checker(patterns):
    compiled = [re.compile(pattern) for pattern in patterns]

    def checker(content, _prev_content):
        return any(pattern.search(content) for pattern in compiled)

    return checker


def check_sql_concat(content, _prev_content):
    if not re.search(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE)\b", content):
        return False
    concat_markers = [r"f[\"']", r"\.format\(", r"[\"']\s*\+", r"\+\s*[\"']", r"%\s*\(", r"%s"]
    return any(re.search(marker, content) for marker in concat_markers)


def check_open_without_context(content, prev_content):
    if not re.search(r"\bopen\s*\(", content):
        return False
    return not (re.search(r"\bwith\b", content) or re.search(r"\bwith\b", prev_content))


CHECKS = [
    (
        "Hardcoded secrets/API keys/tokens",
        make_regex_checker(
            [
                r"AKIA[0-9A-Z]{16}",
                r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*[\"'][A-Za-z0-9+/=_\-]{16,}[\"']",
                r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
            ]
        ),
    ),
    ("SQL built via string concatenation/f-strings/.format()", check_sql_concat),
    (
        "Bare except / empty except or catch blocks",
        make_regex_checker(
            [
                r"^\s*except\s*:\s*(#.*)?$",
                r"^\s*except\b[^:]*:\s*pass\s*(#.*)?$",
                r"catch\s*\([^)]*\)\s*\{\s*\}",
                r"catch\s*\{\s*\}",
            ]
        ),
    ),
    (
        "eval/exec/os.system/subprocess shell=True",
        make_regex_checker(
            [
                r"\beval\s*\(",
                r"\bexec\s*\(",
                r"\bos\.system\s*\(",
                r"subprocess\.(call|run|Popen|check_call|check_output)\([^)]*shell\s*=\s*True",
            ]
        ),
    ),
    (
        "Debug leftovers (print/console.log/debugger/TODO-FIXME-XXX)",
        make_regex_checker(
            [
                r"\bprint\s*\(",
                r"console\.log\s*\(",
                r"\bdebugger\s*;",
                r"\b(TODO|FIXME|XXX)\b",
            ]
        ),
    ),
    ("open() without a context manager [heuristic]", check_open_without_context),
]


def parse_added_lines(diff_text):
    """Return (file, lineno, content, prev_content) for every added line in a unified diff.

    prev_content is the line immediately before it in the resulting file (added or
    context), used by checks that need to look at an adjacent line, e.g. a `with`
    statement on the line above an `open(...)` call.
    """
    results = []
    current_file = None
    new_lineno = None
    in_hunk = False
    last_seen = ""

    for raw in diff_text.split("\n"):
        if raw.startswith("diff --git "):
            current_file = None
            in_hunk = False
            last_seen = ""
            continue
        if raw.startswith("+++ "):
            path = raw[4:].strip()
            if path == "/dev/null":
                current_file = None
            elif path.startswith(("a/", "b/")):
                current_file = path[2:]
            else:
                current_file = path
            last_seen = ""
            continue
        if raw.startswith("--- "):
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            new_lineno = int(match.group(1)) if match else 1
            in_hunk = True
            last_seen = ""
            continue
        if not in_hunk:
            continue

        if raw.startswith("+"):
            if current_file and new_lineno is not None:
                content = raw[1:]
                results.append((current_file, new_lineno, content, last_seen))
                last_seen = content
                new_lineno += 1
        elif raw.startswith("-"):
            continue
        elif raw.startswith("\\"):
            continue
        else:
            content = raw[1:] if raw.startswith(" ") else raw
            last_seen = content
            if new_lineno is not None:
                new_lineno += 1

    return results


def run_checks(added_lines):
    findings = {name: [] for name, _ in CHECKS}
    for file, lineno, content, prev_content in added_lines:
        for name, checker in CHECKS:
            if checker(content, prev_content):
                findings[name].append((file, lineno, content.strip()))
    return findings


def format_report(findings):
    if not any(findings.values()):
        return "No matches found in this diff."

    lines = []
    for i, (name, matches) in enumerate(findings.items(), start=1):
        if not matches:
            lines.append(f"{i}. {name}: Not found")
            continue
        lines.append(f"{i}. {name}:")
        for file, lineno, content in matches:
            lines.append(f"   - {file}:{lineno}: {content}")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("usage: local_review_scan.py <diff-file>", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        diff_text = f.read()

    added_lines = parse_added_lines(diff_text)
    added_lines = [line for line in added_lines if not is_excluded_path(line[0])]
    findings = run_checks(added_lines)
    print(format_report(findings))


if __name__ == "__main__":
    main()
