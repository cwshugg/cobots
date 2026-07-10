"""
test_tags.py - Unit tests for the tag validation and expression engine.

Covers single-tag normalization/validation, the tokenizer, the
recursive-descent parser (grammar, precedence, implicit AND, ``!``/``not``
equivalence, case-insensitivity of operators and tags), the evaluator against
the worked-examples table, `MatchAll` on empty input, reserved-word rejection,
and every documented error case.
"""

import os
import sys
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib is importable regardless of working directory.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.workspace.tags import (
    AndNode,
    MatchAll,
    NotNode,
    OrNode,
    TagError,
    TagLeaf,
    Token,
    TOK_AND,
    TOK_LPAREN,
    TOK_NOT,
    TOK_OR,
    TOK_RPAREN,
    TOK_TAG,
    normalize_tag,
    parse_tag_expression,
    tag_expression_matches,
    tokenize,
    validate_tag,
    validate_tags,
)


# ===================================================================
# normalize_tag
# ===================================================================


class TestNormalizeTag(unittest.TestCase):
    """Verify `normalize_tag` strips whitespace and lowercases."""

    def test_lowercases(self) -> None:
        self.assertEqual(normalize_tag("Git"), "git")

    def test_lowercases_all_caps(self) -> None:
        self.assertEqual(normalize_tag("RUST"), "rust")

    def test_strips_surrounding_whitespace(self) -> None:
        self.assertEqual(normalize_tag("  git  "), "git")

    def test_strips_and_lowercases(self) -> None:
        self.assertEqual(normalize_tag("\tGiT\n"), "git")

    def test_leaves_clean_tag_unchanged(self) -> None:
        self.assertEqual(normalize_tag("a_b-c99"), "a_b-c99")


# ===================================================================
# validate_tag
# ===================================================================


class TestValidateTagAccepts(unittest.TestCase):
    """Verify `validate_tag` accepts well-formed, non-reserved tags."""

    def test_accepts_simple(self) -> None:
        validate_tag("git")  # should not raise

    def test_accepts_digits(self) -> None:
        validate_tag("c99")

    def test_accepts_underscore_and_dash(self) -> None:
        validate_tag("a_b-c")

    def test_accepts_reserved_word_as_substring(self) -> None:
        # Only the bare reserved words are rejected; compounds are fine.
        validate_tag("and_gate")
        validate_tag("not-really")
        validate_tag("oregon")
        validate_tag("android")


class TestValidateTagRejects(unittest.TestCase):
    """Verify `validate_tag` rejects malformed or reserved tags."""

    def test_rejects_empty(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("")

    def test_rejects_internal_space(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("a b")

    def test_rejects_punctuation(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("ru$t")

    def test_rejects_bang(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("!x")

    def test_rejects_unicode(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("caf\u00e9")

    def test_rejects_reserved_and(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("and")

    def test_rejects_reserved_or(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("or")

    def test_rejects_reserved_not(self) -> None:
        with self.assertRaises(TagError):
            validate_tag("not")

    def test_rejects_reserved_word_any_case(self) -> None:
        # validate_tag receives already-normalized tags in practice, but it
        # must still reject reserved words regardless of case defensively.
        for word in ("AND", "Or", "NoT"):
            with self.assertRaises(TagError):
                validate_tag(word)


# ===================================================================
# validate_tags
# ===================================================================


class TestValidateTags(unittest.TestCase):
    """Verify `validate_tags` normalizes, validates, and de-duplicates."""

    def test_lowercases_all(self) -> None:
        self.assertEqual(validate_tags(["Git", "RUST"]), ["git", "rust"])

    def test_dedupes_preserving_first_seen_order(self) -> None:
        result = validate_tags(["git", "rust", "Git", "c"])
        self.assertEqual(result, ["git", "rust", "c"])

    def test_dedupes_case_insensitively(self) -> None:
        self.assertEqual(validate_tags(["Git", "git", "GIT"]), ["git"])

    def test_strips_whitespace(self) -> None:
        self.assertEqual(validate_tags([" git ", "rust "]), ["git", "rust"])

    def test_rejects_empty_list(self) -> None:
        with self.assertRaises(TagError):
            validate_tags([])

    def test_rejects_invalid_member(self) -> None:
        with self.assertRaises(TagError):
            validate_tags(["git", "ru$t"])

    def test_rejects_reserved_member(self) -> None:
        with self.assertRaises(TagError):
            validate_tags(["git", "and"])


# ===================================================================
# tokenize
# ===================================================================


class TestTokenize(unittest.TestCase):
    """Verify the tokenizer emits the correct token stream."""

    def test_tags_and_operators(self) -> None:
        self.assertEqual(
            tokenize("git and !rust"),
            [
                Token(TOK_TAG, "git"),
                Token(TOK_AND),
                Token(TOK_NOT),
                Token(TOK_TAG, "rust"),
            ],
        )

    def test_reserved_words_fold_to_operators_case_insensitively(self) -> None:
        self.assertEqual(
            tokenize("A AND B OR C NOT D"),
            [
                Token(TOK_TAG, "a"),
                Token(TOK_AND),
                Token(TOK_TAG, "b"),
                Token(TOK_OR),
                Token(TOK_TAG, "c"),
                Token(TOK_NOT),
                Token(TOK_TAG, "d"),
            ],
        )

    def test_tag_value_is_lowercased(self) -> None:
        self.assertEqual(tokenize("Git"), [Token(TOK_TAG, "git")])

    def test_parentheses(self) -> None:
        self.assertEqual(
            tokenize("(git)"),
            [Token(TOK_LPAREN), Token(TOK_TAG, "git"), Token(TOK_RPAREN)],
        )

    def test_bang_without_whitespace(self) -> None:
        self.assertEqual(
            tokenize("!git"),
            [Token(TOK_NOT), Token(TOK_TAG, "git")],
        )

    def test_bang_with_whitespace(self) -> None:
        self.assertEqual(
            tokenize("! git"),
            [Token(TOK_NOT), Token(TOK_TAG, "git")],
        )

    def test_empty_yields_no_tokens(self) -> None:
        self.assertEqual(tokenize(""), [])

    def test_whitespace_only_yields_no_tokens(self) -> None:
        self.assertEqual(tokenize("   \t \n"), [])

    def test_comma_is_error(self) -> None:
        with self.assertRaises(TagError):
            tokenize("git , c")

    def test_dollar_is_error(self) -> None:
        with self.assertRaises(TagError):
            tokenize("ru$t")

    def test_ampersand_is_error(self) -> None:
        with self.assertRaises(TagError):
            tokenize("git & c")


# ===================================================================
# parse_tag_expression (AST + precedence)
# ===================================================================


class TestParseAst(unittest.TestCase):
    """Verify the parser builds the expected AST honoring precedence."""

    def test_single_tag(self) -> None:
        self.assertEqual(parse_tag_expression("git"), TagLeaf("git"))

    def test_empty_is_match_all(self) -> None:
        self.assertEqual(parse_tag_expression(""), MatchAll())

    def test_whitespace_is_match_all(self) -> None:
        self.assertEqual(parse_tag_expression("   "), MatchAll())

    def test_and_or_precedence(self) -> None:
        # git and rust or c  ==  (git and rust) or c
        self.assertEqual(
            parse_tag_expression("git and rust or c"),
            OrNode(AndNode(TagLeaf("git"), TagLeaf("rust")), TagLeaf("c")),
        )

    def test_not_binds_tighter_than_and(self) -> None:
        # !git and rust and c  ==  ((not git) and rust) and c
        self.assertEqual(
            parse_tag_expression("!git and rust and c"),
            AndNode(
                AndNode(NotNode(TagLeaf("git")), TagLeaf("rust")),
                TagLeaf("c"),
            ),
        )

    def test_not_keyword_equivalent_to_bang(self) -> None:
        self.assertEqual(
            parse_tag_expression("not git"),
            parse_tag_expression("!git"),
        )

    def test_implicit_and(self) -> None:
        # git rust  ==  git and rust
        self.assertEqual(
            parse_tag_expression("git rust"),
            parse_tag_expression("git and rust"),
        )
        self.assertEqual(
            parse_tag_expression("git rust"),
            AndNode(TagLeaf("git"), TagLeaf("rust")),
        )

    def test_parentheses_override_precedence(self) -> None:
        self.assertEqual(
            parse_tag_expression("git and (rust or c)"),
            AndNode(TagLeaf("git"), OrNode(TagLeaf("rust"), TagLeaf("c"))),
        )

    def test_implicit_and_with_parens(self) -> None:
        # git (rust or c)  ==  git and (rust or c)
        self.assertEqual(
            parse_tag_expression("git (rust or c)"),
            AndNode(TagLeaf("git"), OrNode(TagLeaf("rust"), TagLeaf("c"))),
        )

    def test_operators_case_insensitive(self) -> None:
        self.assertEqual(
            parse_tag_expression("Git AND C"),
            parse_tag_expression("git and c"),
        )

    def test_and_left_associative(self) -> None:
        self.assertEqual(
            parse_tag_expression("a and b and c"),
            AndNode(AndNode(TagLeaf("a"), TagLeaf("b")), TagLeaf("c")),
        )

    def test_or_left_associative(self) -> None:
        self.assertEqual(
            parse_tag_expression("a or b or c"),
            OrNode(OrNode(TagLeaf("a"), TagLeaf("b")), TagLeaf("c")),
        )

    def test_nested_parentheses(self) -> None:
        self.assertEqual(
            parse_tag_expression("((git))"),
            TagLeaf("git"),
        )

    def test_double_negation(self) -> None:
        self.assertEqual(
            parse_tag_expression("not not git"),
            NotNode(NotNode(TagLeaf("git"))),
        )


class TestParseErrors(unittest.TestCase):
    """Verify every documented error case raises `TagError`."""

    def test_trailing_binary_operator(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git and")

    def test_leading_binary_operator(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("or c")

    def test_double_binary_operator(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git and or c")

    def test_unbalanced_open_paren(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git and (rust")

    def test_unbalanced_close_paren(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git)")

    def test_empty_parentheses(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git and ()")

    def test_bare_empty_parentheses(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("()")

    def test_comma_syntax(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git , c")

    def test_deeply_nested_parens_raise_tagerror(self) -> None:
        # Pathological nesting must raise TagError, not RecursionError, so
        # callers convert it to a clean exit-2 error (report 6378212b, #4).
        with self.assertRaises(TagError):
            parse_tag_expression("(" * 5000)

    def test_deeply_chained_not_raises_tagerror(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("!" * 5000 + "git")

    def test_deeply_nested_input_does_not_raise_recursionerror(self) -> None:
        # Belt-and-suspenders: the guard fires before the C stack overflows.
        try:
            parse_tag_expression("(" * 100000)
        except TagError:
            pass
        except RecursionError:
            self.fail("RecursionError leaked past the depth guard")

    def test_bare_and_operator(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("and")

    def test_trailing_not_operator(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("git and not")

    def test_invalid_character(self) -> None:
        with self.assertRaises(TagError):
            parse_tag_expression("ru$t")


# ===================================================================
# tag_expression_matches (evaluation)
# ===================================================================


# Worked-examples entries from the architecture (§7.3); tags lowercased.
_E1 = ["git", "c"]
_E2 = ["git", "c", "rust"]
_E3 = ["git", "python"]
_E4 = ["python"]


def _matches(expr_str: str, tags: list[str]) -> bool:
    """Parses *expr_str* and evaluates it against *tags* (test helper)."""
    return tag_expression_matches(tags, parse_tag_expression(expr_str))


class TestEvaluationWorkedExamples(unittest.TestCase):
    """Verify evaluation against the §7.3 worked-examples table."""

    def test_or(self) -> None:
        self.assertTrue(_matches("git or rust", _E1))
        self.assertTrue(_matches("git or rust", _E2))
        self.assertTrue(_matches("git or rust", _E3))
        self.assertFalse(_matches("git or rust", _E4))

    def test_and_with_parens(self) -> None:
        self.assertTrue(_matches("git and (rust or c)", _E1))
        self.assertTrue(_matches("git and (rust or c)", _E2))
        self.assertFalse(_matches("git and (rust or c)", _E3))
        self.assertFalse(_matches("git and (rust or c)", _E4))

    def test_not_and_chain_matches_nothing(self) -> None:
        for tags in (_E1, _E2, _E3, _E4):
            self.assertFalse(_matches("!git AND rust and c", tags))

    def test_implicit_and(self) -> None:
        self.assertFalse(_matches("git rust", _E1))
        self.assertTrue(_matches("git rust", _E2))
        self.assertFalse(_matches("git rust", _E3))
        self.assertFalse(_matches("git rust", _E4))

    def test_not(self) -> None:
        self.assertFalse(_matches("not git", _E1))
        self.assertFalse(_matches("not git", _E2))
        self.assertFalse(_matches("not git", _E3))
        self.assertTrue(_matches("not git", _E4))

    def test_case_insensitive_operands(self) -> None:
        self.assertTrue(_matches("Git AND C", _E1))
        self.assertTrue(_matches("Git AND C", _E2))
        self.assertFalse(_matches("Git AND C", _E3))

    def test_match_all_on_empty(self) -> None:
        for tags in (_E1, _E2, _E3, _E4):
            self.assertTrue(_matches("", tags))


class TestEvaluationCaseFolding(unittest.TestCase):
    """Verify evaluation folds entry tags to lowercase."""

    def test_mixed_case_entry_tags_match(self) -> None:
        # Even if a file was hand-edited with mixed-case tags, matching folds.
        self.assertTrue(_matches("git", ["Git", "C"]))
        self.assertTrue(_matches("Git", ["GIT"]))

    def test_bang_equivalent_to_not_in_evaluation(self) -> None:
        for tags in (_E1, _E4):
            self.assertEqual(
                _matches("!git", tags),
                _matches("not git", tags),
            )


if __name__ == "__main__":
    unittest.main()
