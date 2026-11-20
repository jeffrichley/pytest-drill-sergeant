"""What a file's tokens say that its syntax tree doesn't: comments, read once.

A file is tokenized once per analysis. Its comments feed both the inline waivers
and the AAA comment check (DS108); where each `def` line's signature closes, and
which lines hold code, are found in the same pass. Only real comments count: text in a string never does.
"""

import io
import tokenize
from collections.abc import Mapping
from dataclasses import dataclass

# Tokens that are layout or comment, never code.
_NOT_CODE = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
)


@dataclass(frozen=True)
class Comment:
    """A comment, as `tokenize` reads it, so never text in a string.

    Attributes:
        line: The line it is on.
        text: The comment, `#` included.
        alone: Whether it stands alone on its line, with no code before it.
    """

    line: int
    text: str
    alone: bool = True


@dataclass(frozen=True)
class Tokens:
    """What a file's tokens say.

    Attributes:
        comments: Every comment, in line order.
        signature_ends: For each `def` line, the line its signature closes on
            (the `):` of a wrapped signature); the same line when it isn't wrapped.
        code_lines: The lines holding code: every line but blank and comment-only
            ones. Each line a multi-line string spans holds code.
    """

    comments: tuple[Comment, ...]
    signature_ends: Mapping[int, int]
    code_lines: frozenset[int]


def read(source: bytes) -> Tokens:
    """Tokenize a file's source once, for everything `Tokens` holds."""
    comments: list[Comment] = []
    ends: dict[int, int] = {}
    code: set[int] = set()
    open_def: int | None = None
    depth = 0
    for token in tokenize.tokenize(io.BytesIO(source).readline):
        if token.type not in _NOT_CODE:
            code.update(range(token.start[0], token.end[0] + 1))
        if token.type == tokenize.COMMENT:
            alone = not token.line[: token.start[1]].strip()
            comments.append(Comment(token.start[0], token.string, alone))
        elif token.type == tokenize.NAME and token.string == "def" and depth == 0:
            open_def = token.start[0]
        elif token.type == tokenize.OP and open_def is not None:
            if token.string in {"(", "[", "{"}:
                depth += 1
            elif token.string in {")", "]", "}"}:
                depth -= 1
            elif token.string == ":" and depth == 0:
                ends[open_def] = token.start[0]
                open_def = None
    return Tokens(
        comments=tuple(comments), signature_ends=ends, code_lines=frozenset(code)
    )
