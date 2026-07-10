"""
tags.py - Tag validation and the shared boolean tag-expression engine.

This module owns two responsibilities used across the knowledge base skill:

1. Single-tag validation and normalization used on the write path
   (``create`` / ``edit``): `normalize_tag`, `validate_tag`, `validate_tags`.
2. The full boolean **tag-expression** parser and evaluator used identically
   by ``query --tags`` and ``list --tags``: a tokenizer, a recursive-descent
   parser that produces a small AST of predicate nodes, and an evaluator.

There is exactly one parser/evaluator; both commands import it so their tag
matching behaviour is guaranteed to stay in lock-step.

The grammar (EBNF)::

    expression = or_expr ;
    or_expr    = and_expr , { "or" , and_expr } ;
    and_expr   = not_expr , { [ "and" ] , not_expr } ;  (* omitted op = AND *)
    not_expr   = ( "not" | "!" ) , not_expr | primary ;
    primary    = "(" , expression , ")" | TAG ;
    TAG        = ( letter | digit | "_" | "-" )+ ;      (* not reserved *)

Operator keywords are case-insensitive; precedence is ``not`` > ``and`` >
``or``; binary operators are left-associative; parentheses nest arbitrarily;
adjacency implies ``and``. An empty (or whitespace-only) expression is not an
error - it yields `MatchAll`, which matches every entry.

The module is pure (no filesystem or network access) so it can be unit tested
in isolation.
"""

import re
from dataclasses import dataclass


# Character class for a single valid tag: ASCII letters, digits, underscore,
# and dash. Fixed code constant (NOT workspace-configurable) so that tag
# validation stays invariant across every workspace.
TAG_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Reserved words that may not be used as bare tag names, because they are
# grammar operators. Compared case-insensitively against a lowercased tag.
RESERVED_WORDS = frozenset({"and", "or", "not"})


class TagError(ValueError):
    """Raised on an invalid tag or a malformed tag expression."""


# ---------------------------------------------------------------------------
# Single-tag validation / normalization (write path)
# ---------------------------------------------------------------------------

def normalize_tag(tag: str) -> str:
    """Canonicalizes a tag by stripping surrounding whitespace and
    lowercasing it.

    Tags are canonicalized to lowercase both when written to disk and
    whenever read or interpreted, so matching is case-insensitive end to
    end.
    """
    return tag.strip().lower()


def validate_tag(tag: str) -> None:
    """Validates a single (already normalized) tag, raising on failure.

    Raises:
        TagError: if *tag* is empty, contains characters outside `TAG_RE`,
            or is one of the `RESERVED_WORDS` (checked case-insensitively).
    """
    if not tag:
        raise TagError("tag must not be empty")

    if tag.lower() in RESERVED_WORDS:
        raise TagError(
            f"tag {tag!r} is a reserved word and cannot be used as a tag name"
        )

    if not TAG_RE.match(tag):
        raise TagError(
            f"tag {tag!r} is invalid: tags may contain only letters, "
            f"digits, underscores, and dashes"
        )


def validate_tags(tags: list[str]) -> list[str]:
    """Normalizes, validates, and de-duplicates a list of tags.

    Each tag is lowercased via `normalize_tag`, validated via `validate_tag`,
    and duplicates are removed while preserving first-seen order. At least one
    valid tag is required.

    Args:
        tags: The raw tag strings to clean.

    Returns:
        The cleaned, lowercased, de-duplicated list suitable for frontmatter.

    Raises:
        TagError: if the resulting list would be empty, or if any tag is
            invalid or reserved.
    """
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = normalize_tag(raw)
        validate_tag(tag)
        if tag not in seen:
            seen.add(tag)
            cleaned.append(tag)

    if not cleaned:
        raise TagError("at least one tag is required")

    return cleaned


# ---------------------------------------------------------------------------
# Tag-expression AST
# ---------------------------------------------------------------------------

class TagExpr:
    """Base class for tag-expression AST nodes.

    Every node exposes `eval`, which reports whether the node matches a given
    set of (lowercased) entry tags.
    """

    def eval(self, tagset: set[str]) -> bool:
        """Evaluates this node against *tagset*, returning a match boolean."""
        raise NotImplementedError


@dataclass(frozen=True)
class MatchAll(TagExpr):
    """Matches every entry; produced by an empty expression."""

    def eval(self, tagset: set[str]) -> bool:
        """Always matches."""
        return True


@dataclass(frozen=True)
class TagLeaf(TagExpr):
    """Matches iff *tag* is present in the entry's (lowercased) tag set."""

    tag: str

    def eval(self, tagset: set[str]) -> bool:
        """Matches when this leaf's tag is in *tagset*."""
        return self.tag in tagset


@dataclass(frozen=True)
class NotNode(TagExpr):
    """Logical negation of its child node."""

    child: TagExpr

    def eval(self, tagset: set[str]) -> bool:
        """Matches when the child does not."""
        return not self.child.eval(tagset)


@dataclass(frozen=True)
class AndNode(TagExpr):
    """Logical conjunction of two child nodes."""

    left: TagExpr
    right: TagExpr

    def eval(self, tagset: set[str]) -> bool:
        """Matches when both children match."""
        return self.left.eval(tagset) and self.right.eval(tagset)


@dataclass(frozen=True)
class OrNode(TagExpr):
    """Logical disjunction of two child nodes."""

    left: TagExpr
    right: TagExpr

    def eval(self, tagset: set[str]) -> bool:
        """Matches when either child matches."""
        return self.left.eval(tagset) or self.right.eval(tagset)


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Token kind identifiers.
TOK_TAG = "TAG"
TOK_AND = "AND"
TOK_OR = "OR"
TOK_NOT = "NOT"
TOK_LPAREN = "LPAREN"
TOK_RPAREN = "RPAREN"

# Maps a reserved word (lowercased) to its operator token kind.
_RESERVED_TOKEN_KINDS = {
    "and": TOK_AND,
    "or": TOK_OR,
    "not": TOK_NOT,
}

# Character class used to scan a maximal run of tag characters.
_TAG_CHAR_RE = re.compile(r"[A-Za-z0-9_-]")


@dataclass(frozen=True)
class Token:
    """A single lexical token: a kind and, for tags, a lowercased value."""

    kind: str
    value: str = ""


def tokenize(expr: str) -> list[Token]:
    """Splits a tag-expression string into a list of `Token` objects.

    Whitespace separates tokens but never produces one. ``(``/``)`` become
    parentheses, ``!`` becomes a `TOK_NOT`, the bare words ``and``/``or``/
    ``not`` (case-insensitive) become their operator tokens, and any other
    maximal run of tag characters becomes a lowercased `TOK_TAG`.

    Raises:
        TagError: on any character that is not whitespace, a parenthesis,
            ``!``, or a tag character.
    """
    tokens: list[Token] = []
    i = 0
    length = len(expr)
    while i < length:
        ch = expr[i]

        # Whitespace is a separator only.
        if ch.isspace():
            i += 1
            continue

        # Single-character structural / operator tokens.
        if ch == "(":
            tokens.append(Token(TOK_LPAREN))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token(TOK_RPAREN))
            i += 1
            continue
        if ch == "!":
            tokens.append(Token(TOK_NOT))
            i += 1
            continue

        # A maximal run of tag characters: either an operator keyword or a tag.
        if _TAG_CHAR_RE.match(ch):
            start = i
            while i < length and _TAG_CHAR_RE.match(expr[i]):
                i += 1
            word = expr[start:i]
            lowered = word.lower()
            reserved_kind = _RESERVED_TOKEN_KINDS.get(lowered)
            if reserved_kind is not None:
                tokens.append(Token(reserved_kind))
            else:
                tokens.append(Token(TOK_TAG, lowered))
            continue

        # Anything else (comma, '$', '&', etc.) is invalid.
        raise TagError(
            f"invalid character {ch!r} in tag expression {expr!r}"
        )

    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------

# Token kinds that can begin a `not_expr` (and therefore an implicit AND).
_OPERAND_START_KINDS = frozenset({TOK_TAG, TOK_NOT, TOK_LPAREN})

# Maximum nesting depth for a tag expression. The recursive-descent parser
# recurses once per level of parenthesis nesting and once per chained unary
# `not`/`!`. Pathological input (e.g. thousands of `(` or `!`) would otherwise
# exhaust Python's C stack and raise an uncatchable-by-`TagError`
# `RecursionError`, aborting with a traceback (security report 6378212b,
# finding 4). This bound is far above any realistic hand-written expression
# while staying comfortably under the interpreter's recursion limit.
_MAX_PARSE_DEPTH = 200


class _Parser:
    """Recursive-descent parser over a token list.

    One method per precedence level mirrors the grammar: `_parse_or` ->
    `_parse_and` -> `_parse_not` -> `_parse_primary`. The parser is an
    internal helper; callers use `parse_tag_expression`.
    """

    def __init__(self, tokens: list[Token]) -> None:
        """Stores the token list and initializes the read cursor."""
        self._tokens = tokens
        self._pos = 0
        # Current recursion/nesting depth, bounded by `_MAX_PARSE_DEPTH`.
        self._depth = 0

    def _enter(self) -> None:
        """Records descent into a nesting level, guarding against overflow.

        Raises:
            TagError: if the expression nests deeper than `_MAX_PARSE_DEPTH`,
                converting what would be a `RecursionError` crash into a
                clean input error.
        """
        self._depth += 1
        if self._depth > _MAX_PARSE_DEPTH:
            raise TagError("tag expression is nested too deeply")

    def _leave(self) -> None:
        """Records ascent out of a nesting level."""
        self._depth -= 1

    def _peek(self) -> Token | None:
        """Returns the current token without consuming it, or ``None``."""
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> Token:
        """Consumes and returns the current token."""
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def parse(self) -> TagExpr:
        """Parses the full token stream into a `TagExpr`.

        Raises:
            TagError: on any syntax error, including trailing tokens left
                over after a complete expression (e.g. an unbalanced ``)``).
        """
        # An empty token stream matches everything.
        if not self._tokens:
            return MatchAll()

        node = self._parse_or()

        # No tokens may remain; a leftover token is a syntax error.
        remaining = self._peek()
        if remaining is not None:
            raise TagError(
                f"unexpected token {remaining.kind} in tag expression"
            )
        return node

    def _parse_or(self) -> TagExpr:
        """Parses an ``or``-level (lowest precedence) expression."""
        node = self._parse_and()
        while True:
            token = self._peek()
            if token is None or token.kind != TOK_OR:
                break
            self._advance()  # consume OR
            right = self._parse_and()
            node = OrNode(node, right)
        return node

    def _parse_and(self) -> TagExpr:
        """Parses an ``and``-level expression, honoring implicit AND."""
        node = self._parse_not()
        while True:
            token = self._peek()
            if token is None:
                break
            if token.kind == TOK_AND:
                self._advance()  # consume explicit AND
                right = self._parse_not()
                node = AndNode(node, right)
                continue
            # Adjacency: a new operand with no operator implies AND.
            if token.kind in _OPERAND_START_KINDS:
                right = self._parse_not()
                node = AndNode(node, right)
                continue
            break
        return node

    def _parse_not(self) -> TagExpr:
        """Parses a ``not``-level (highest precedence) expression."""
        token = self._peek()
        if token is not None and token.kind == TOK_NOT:
            self._advance()  # consume NOT
            self._enter()
            try:
                child = self._parse_not()
            finally:
                self._leave()
            return NotNode(child)
        return self._parse_primary()

    def _parse_primary(self) -> TagExpr:
        """Parses a parenthesized group or a single tag leaf."""
        token = self._peek()
        if token is None:
            raise TagError(
                "unexpected end of tag expression: operand expected"
            )

        if token.kind == TOK_LPAREN:
            self._advance()  # consume '('
            self._enter()
            try:
                node = self._parse_or()
            finally:
                self._leave()
            closing = self._peek()
            if closing is None or closing.kind != TOK_RPAREN:
                raise TagError("unbalanced parentheses in tag expression")
            self._advance()  # consume ')'
            return node

        if token.kind == TOK_TAG:
            self._advance()
            return TagLeaf(token.value)

        # A binary operator, stray ')', or anything else here is an error.
        raise TagError(
            f"unexpected token {token.kind} where an operand was expected"
        )


def parse_tag_expression(expr: str) -> TagExpr:
    """Parses a tag-expression string into a `TagExpr` AST.

    An empty or whitespace-only expression yields `MatchAll`. Any syntax
    error - unbalanced parentheses, a dangling/leading/trailing binary
    operator, empty parentheses, or an invalid tag character - raises
    `TagError`. Excessively nested input also raises `TagError` (via the
    parser's depth guard, with a `RecursionError` catch as a final
    safety net) rather than crashing with a traceback.
    """
    tokens = tokenize(expr)
    try:
        return _Parser(tokens).parse()
    except RecursionError:
        raise TagError("tag expression is nested too deeply") from None


def tag_expression_matches(entry_tags: list[str], expr: TagExpr) -> bool:
    """Evaluates a parsed tag expression against an entry's tags.

    The entry tags are lowercased into a set (so matching is
    case-insensitive even if a file was hand-edited with mixed case) and the
    expression is evaluated against that set.
    """
    tagset = {tag.strip().lower() for tag in entry_tags}
    return expr.eval(tagset)
