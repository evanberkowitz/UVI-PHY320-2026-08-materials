"""Solution markers, and the two ways to resolve them.

A marker block, in a .py file or a notebook code cell.  Every line of the
sketch below is itself commented out, so that no line of this docstring is
a bare marker token: this module is the definition of the grammar, and it
must never read as an instance of it.

    # ### BEGIN SOLUTION
    # <solution arm>
    # ### ELSE
    # <else arm; every line commented>
    # ### END SOLUTION

The private source keeps both arms, so it must stay executable.  That is
why every line of a code ELSE arm must be commented: an uncommented
`raise NotImplementedError` would run whenever the solution above it did
not return first, breaking the very notebook the solution was written in.
On the way out, one leading `#` is removed from each line, so `#` marks
code-in-waiting and `##` marks commentary that survives as commentary.

`strip` produces what students get.  `keep` produces the solution.
Neither can emit a marker.
"""

STRIP = "strip"
KEEP = "keep"

DEFAULT_STUB = 'raise NotImplementedError("your code here")'
SOLUTION_TAG = "solution"

CODE_BEGIN, CODE_ELSE, CODE_END = (
    "### BEGIN SOLUTION",
    "### ELSE",
    "### END SOLUTION",
)
TEXT_BEGIN, TEXT_ELSE, TEXT_END = (
    "<!-- BEGIN SOLUTION -->",
    "<!-- ELSE -->",
    "<!-- END SOLUTION -->",
)


class MarkerError(Exception):
    """A marker block that cannot be resolved.  Never recovered from."""

    def __init__(self, message, lineno):
        super().__init__(message)
        self.lineno = lineno


def _fail(message, lineno):
    """Raise with the line number attached, once, so callers can prefix freely."""
    raise MarkerError(f"line {lineno}: {message}", lineno)


def indentation(line):
    return line[: len(line) - len(line.lstrip())]


def uncomment(line, lineno):
    """Remove one leading '#', and one following space, keeping indentation."""
    body = line.strip()
    if not body:
        return ""
    if not body.startswith("#"):
        _fail(
            "every line of a code ELSE arm must be commented, "
            f"and this one is not: {body!r}",
            lineno,
        )
    body = body[1:]
    if body.startswith(" "):
        body = body[1:]
    return indentation(line) + body


def verbatim(line, lineno):
    return line


def _transform(lines, mode, begin, otherwise, end, resolve_else, stub):
    out = []
    state = "outside"
    arm_indent = ""
    seen_else = False

    for lineno, line in enumerate(lines, start=1):
        token = line.strip()

        if token == begin:
            if state != "outside":
                _fail("nested BEGIN SOLUTION", lineno)
            state, arm_indent, seen_else = "solution", indentation(line), False
            continue

        if token == otherwise:
            if state == "outside":
                _fail("ELSE outside a solution block", lineno)
            if seen_else:
                _fail("second ELSE in one block", lineno)
            state, seen_else = "else", True
            continue

        if token == end:
            if state == "outside":
                _fail("END SOLUTION without BEGIN SOLUTION", lineno)
            if mode == STRIP and not seen_else and stub is not None:
                out.append(arm_indent + stub)
            state = "outside"
            continue

        if state == "outside":
            out.append(line)
        elif state == "solution":
            if mode == KEEP:
                out.append(line)
        else:
            # Resolve in both modes, so that a malformed ELSE arm is an
            # error even when the mode would have discarded it.
            resolved = resolve_else(line, lineno)
            if mode == STRIP:
                out.append(resolved)

    if state != "outside":
        _fail("BEGIN SOLUTION without END SOLUTION", len(lines))

    return out


def transform_code(lines, mode):
    """Resolve marker blocks in Python source, given as lines without newlines."""
    return _transform(
        lines, mode, CODE_BEGIN, CODE_ELSE, CODE_END,
        resolve_else=uncomment, stub=DEFAULT_STUB,
    )


def transform_markdown(lines, mode):
    """Resolve marker blocks in markdown.

    Prose is never executed, so an ELSE arm needs no comment escaping and
    is taken verbatim.  There is no default stub: a question with no ELSE
    arm simply loses its answer.
    """
    return _transform(
        lines, mode, TEXT_BEGIN, TEXT_ELSE, TEXT_END,
        resolve_else=verbatim, stub=None,
    )
