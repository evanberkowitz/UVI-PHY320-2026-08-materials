"""Independently re-check a tree for anything that should not be published.

Deliberately not built on the scrubber: a bug there must not be able to
disable its own check.  This runs over what was actually written, and any
finding aborts the publish before a commit exists.

**Broader than the grammar, on purpose.**  The scrubber must match markers
exactly, because it rewrites what it matches and a loose match would mangle
ordinary code.  The audit only ever flags, so it can afford to be generous:
it matches case-insensitively and tolerates missing or doubled spaces.  That
is the point.  An instructor who types `### begin solution` writes a block
the scrubber does not recognise, so the solution passes straight through; if
the audit were equally strict it would wave that through as well.  The
mismatch is the whole reason this file exists.

Two directories are skipped.  `.git`, `__pycache__` and `.ipynb_checkpoints`
are not published, at any depth.  The `tool/` package **at the root** is the
one place a marker token legitimately appears as a string literal — it is
where the grammar is defined — so it is skipped there and only there, and
its three published files are copied verbatim rather than scrubbed and are
covered by their own tests.  Every other published file is audited.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from tool.markers import SOLUTION_TAG

# `### ELSE` carries no SOLUTION word, so it gets its own alternative with a
# word boundary; without one, a heading like "## Elsewhere" would be flagged.
# For the same reason BEGIN and END must be followed by SOLUTION: "##
# Beginning" is a plausible heading and must not abort a publish.
_MARKER = (
    r"#{2,}[ \t]*(?:BEGIN|END)[ \t]*SOLUTIONS?\b"
    r"|#{2,}[ \t]*ELSE\b"
    r"|<!--[ \t]*(?:BEGIN|END)[ \t]*SOLUTIONS?\b"
    r"|<!--[ \t]*ELSE[ \t]*-->"
)

MARKER_PATTERN = re.compile(_MARKER, re.IGNORECASE)
MARKER_BYTES = re.compile(_MARKER.encode("ascii"), re.IGNORECASE)

SKIP_DIRECTORIES = {".git", ".ipynb_checkpoints", "__pycache__"}
SKIP_ROOTS = {"tool"}


@dataclass(frozen=True)
class Leak:
    path: Path
    detail: str


def _markers_in(text, pattern):
    """Distinct marker-ish strings in `text`, in the order they appear."""
    found = []
    for match in pattern.finditer(text):
        hit = match.group(0)
        if isinstance(hit, bytes):
            hit = hit.decode("utf-8", errors="replace")
        if hit not in found:
            found.append(hit)
    return found


def _audit_notebook(path):
    leaks = []
    try:
        nb = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        return [Leak(path, f"unreadable notebook: {error}")]

    if not isinstance(nb, dict):
        return [Leak(path, f"malformed notebook: top level is {type(nb).__name__}, not dict")]

    for number, cell in enumerate(nb.get("cells", []), start=1):
        try:
            source = cell.get("source", "")
            text = "".join(source) if isinstance(source, list) else source
            for hit in _markers_in(text, MARKER_PATTERN):
                leaks.append(Leak(path, f"cell {number} contains {hit!r}"))
            if SOLUTION_TAG in cell.get("metadata", {}).get("tags", []):
                leaks.append(Leak(path, f"cell {number} still tagged {SOLUTION_TAG!r}"))
            if cell.get("outputs"):
                leaks.append(Leak(path, f"cell {number} has saved outputs"))
            if cell.get("execution_count") is not None:
                leaks.append(Leak(path, f"cell {number} has an execution_count"))
        except (AttributeError, TypeError) as error:
            leaks.append(Leak(path, f"cell {number} is malformed: {error}"))
    return leaks


def _audit_text(path):
    """Search a file's raw bytes for marker tokens.

    Reading bytes rather than decoding text means a binary dataset under
    `data/` is not mistaken for an unreadable file just because it is not
    UTF-8: markers are still caught whatever the encoding, and undecodable
    content is no longer conflated with content this function could not
    read at all.
    """
    try:
        content = path.read_bytes()
    except OSError as error:
        return [Leak(path, f"unreadable file: {error}")]
    return [
        Leak(path, f"contains {hit!r}")
        for hit in _markers_in(content, MARKER_BYTES)
    ]


def _skipped(relative):
    parts = relative.parts
    if SKIP_DIRECTORIES & set(parts[:-1]):
        return True
    return bool(parts[:1]) and parts[0] in SKIP_ROOTS


def find_leaks(root):
    """Every reason `root` must not be published, in path order."""
    root = Path(root)
    leaks = []
    try:
        paths = sorted(root.rglob("*"))
    except OSError as error:
        return [Leak(root, f"cannot scan directory: {error}")]

    for path in paths:
        if not path.is_file():
            continue
        # Relative to the tree being audited: testing the root-prefixed path
        # would let an ancestor directory that happens to be named `tool` or
        # `.git` switch the entire audit off.
        if _skipped(path.relative_to(root)):
            continue
        if path.suffix == ".ipynb":
            leaks.extend(_audit_notebook(path))
        else:
            leaks.extend(_audit_text(path))
    return leaks


def main(argv=None):
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Fail if a tree contains anything that must not be published."
    )
    parser.add_argument("root", nargs="?", default=".")
    arguments = parser.parse_args(argv)

    leaks = find_leaks(Path(arguments.root))
    for leak in leaks:
        print(f"{leak.path}: {leak.detail}", file=sys.stderr)
    if leaks:
        print(f"\n{len(leaks)} problem(s) found.", file=sys.stderr)
        return 1
    print("clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
