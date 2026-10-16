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

Markdown has a second kind of block, for a question whose prompt both
versions share.  The prompt comes first, so it is written once:

    <!-- QUESTION -->
    <prompt; in both versions>
    <!-- ANSWER -->
    <answer; in the solution only>
    <!-- END QUESTION -->

`strip` produces what students get.  `keep` produces the solution.
Neither can emit a marker.
"""

from dataclasses import dataclass
from typing import NoReturn

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
QUESTION_BEGIN, QUESTION_ANSWER, QUESTION_END = (
    "<!-- QUESTION -->",
    "<!-- ANSWER -->",
    "<!-- END QUESTION -->",
)


class MarkerError(Exception):
    """A marker block that cannot be resolved.  Never recovered from."""

    def __init__(self, message, lineno):
        super().__init__(message)
        self.lineno = lineno


def _fail(message, lineno) -> NoReturn:
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


@dataclass(frozen=True)
class Grammar:
    """One kind of two-armed block, and which arms each mode keeps.

    `names` spell the three tokens in error messages, `noun` names the
    block, and `keeps[mode]` says whether the first and second arm survive.
    `resolve` is applied to every line of the second arm, in both modes,
    so that a malformed one is an error even when the mode discards it.
    """

    begin: str
    middle: str
    end: str
    names: tuple
    noun: str
    keeps: dict
    resolve: object
    stub: object = None
    require_middle: bool = False


def _transform(lines, mode, grammars):
    out = []
    block = None
    arm_indent = ""
    second = False

    for lineno, line in enumerate(lines, start=1):
        token = line.strip()
        matched = next(
            ((grammar, role)
             for grammar in grammars
             for role, spelling in enumerate((grammar.begin, grammar.middle, grammar.end))
             if token == spelling),
            None,
        )

        if matched is None:
            if block is None:
                out.append(line)
                continue
            keep_first, keep_second = block.keeps[mode]
            if not second:
                if keep_first:
                    out.append(line)
            else:
                resolved = block.resolve(line, lineno)
                if keep_second:
                    out.append(resolved)
            continue

        grammar, role = matched
        begin_name, middle_name, end_name = grammar.names

        if block is not None and grammar is not block:
            _fail(f"{grammar.names[role]} inside a {block.noun}", lineno)

        if role == 0:
            if block is not None:
                _fail(f"nested {begin_name}", lineno)
            block, arm_indent, second = grammar, indentation(line), False
        elif role == 1:
            if block is None:
                _fail(f"{middle_name} outside a {grammar.noun}", lineno)
            if second:
                _fail(f"second {middle_name} in one block", lineno)
            second = True
        else:
            if block is None:
                _fail(f"{end_name} without {begin_name}", lineno)
            if not second and block.require_middle:
                _fail(f"{begin_name} without {middle_name}", lineno)
            if mode == STRIP and not second and block.stub is not None:
                out.append(arm_indent + block.stub)
            block = None

    if block is not None:
        _fail(f"{block.names[0]} without {block.names[2]}", len(lines))

    return out


# The solution arm comes first and the student's arm second.
_SOLUTION_KEEPS = {STRIP: (False, True), KEEP: (True, False)}

CODE_GRAMMAR = Grammar(
    CODE_BEGIN, CODE_ELSE, CODE_END,
    names=("BEGIN SOLUTION", "ELSE", "END SOLUTION"),
    noun="solution block",
    keeps=_SOLUTION_KEEPS,
    resolve=uncomment,
    stub=DEFAULT_STUB,
)

TEXT_GRAMMAR = Grammar(
    TEXT_BEGIN, TEXT_ELSE, TEXT_END,
    names=("BEGIN SOLUTION", "ELSE", "END SOLUTION"),
    noun="solution block",
    keeps=_SOLUTION_KEEPS,
    resolve=verbatim,
)

# The prompt comes first and is in both versions; the answer is the key's alone.
QUESTION_GRAMMAR = Grammar(
    QUESTION_BEGIN, QUESTION_ANSWER, QUESTION_END,
    names=("QUESTION", "ANSWER", "END QUESTION"),
    noun="question block",
    keeps={STRIP: (True, False), KEEP: (True, True)},
    resolve=verbatim,
    require_middle=True,
)


def transform_code(lines, mode):
    """Resolve marker blocks in Python source, given as lines without newlines."""
    return _transform(lines, mode, [CODE_GRAMMAR])


def transform_markdown(lines, mode):
    """Resolve marker blocks in markdown.

    Prose is never executed, so an ELSE arm needs no comment escaping and
    is taken verbatim.  There is no default stub: a question with no ELSE
    arm simply loses its answer.

    Question blocks are resolved in the same pass, so a question inside a
    solution block, or a solution inside a question, is an error.
    """
    return _transform(lines, mode, [TEXT_GRAMMAR, QUESTION_GRAMMAR])
