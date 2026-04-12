"""
test_topic.py - Unit tests for the random ntfy topic generation.

Verifies that `generate_default_topic()` produces strings with the
correct prefix, length, and character set.
"""

import os
import string
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

from cobots_lib.workspace.topic import (
    TOPIC_ALPHABET,
    TOPIC_PREFIX,
    TOPIC_RANDOM_LENGTH,
    generate_default_topic,
)

# The expected total length of a generated topic string.
EXPECTED_TOTAL_LENGTH = len(TOPIC_PREFIX) + TOPIC_RANDOM_LENGTH


class TestGenerateDefaultTopicFormat(unittest.TestCase):
    """Verify that the generated topic has the correct structure."""

    def test_starts_with_prefix(self) -> None:
        """The topic must begin with the configured prefix."""
        topic = generate_default_topic()
        self.assertTrue(
            topic.startswith(TOPIC_PREFIX),
            f"Topic {topic!r} does not start with {TOPIC_PREFIX!r}",
        )

    def test_total_length(self) -> None:
        """The topic must be exactly 37 characters long."""
        topic = generate_default_topic()
        self.assertEqual(
            len(topic),
            EXPECTED_TOTAL_LENGTH,
            f"Expected length {EXPECTED_TOTAL_LENGTH}, "
            f"got {len(topic)} for {topic!r}",
        )

    def test_random_part_length(self) -> None:
        """The random portion (after the prefix) must be exactly 30
        characters.
        """
        topic = generate_default_topic()
        random_part = topic[len(TOPIC_PREFIX):]
        self.assertEqual(len(random_part), TOPIC_RANDOM_LENGTH)

    def test_random_part_is_alphanumeric(self) -> None:
        """Every character in the random portion must be a letter or
        digit.
        """
        topic = generate_default_topic()
        random_part = topic[len(TOPIC_PREFIX):]
        allowed = set(string.ascii_letters + string.digits)
        for ch in random_part:
            self.assertIn(
                ch,
                allowed,
                f"Character {ch!r} in {random_part!r} is not "
                f"alphanumeric",
            )


class TestGenerateDefaultTopicUniqueness(unittest.TestCase):
    """Verify that successive calls produce distinct topics."""

    def test_two_calls_produce_different_topics(self) -> None:
        """Two consecutive calls should almost certainly differ."""
        a = generate_default_topic()
        b = generate_default_topic()
        self.assertNotEqual(
            a,
            b,
            "Two generated topics should not be identical",
        )

    def test_many_calls_all_unique(self) -> None:
        """100 generated topics must all be distinct."""
        topics = {generate_default_topic() for _ in range(100)}
        self.assertEqual(len(topics), 100)


class TestGenerateDefaultTopicCharacterDistribution(unittest.TestCase):
    """Verify that the random portion uses the full alphabet over
    many samples.
    """

    def test_contains_uppercase(self) -> None:
        """At least one topic out of many should contain an uppercase
        letter in the random portion.
        """
        found = False
        for _ in range(50):
            random_part = generate_default_topic()[len(TOPIC_PREFIX):]
            if any(c in string.ascii_uppercase for c in random_part):
                found = True
                break
        self.assertTrue(found, "No uppercase letter found in 50 topics")

    def test_contains_lowercase(self) -> None:
        """At least one topic out of many should contain a lowercase
        letter in the random portion.
        """
        found = False
        for _ in range(50):
            random_part = generate_default_topic()[len(TOPIC_PREFIX):]
            if any(c in string.ascii_lowercase for c in random_part):
                found = True
                break
        self.assertTrue(found, "No lowercase letter found in 50 topics")

    def test_contains_digit(self) -> None:
        """At least one topic out of many should contain a digit in
        the random portion.
        """
        found = False
        for _ in range(50):
            random_part = generate_default_topic()[len(TOPIC_PREFIX):]
            if any(c in string.digits for c in random_part):
                found = True
                break
        self.assertTrue(found, "No digit found in 50 topics")


class TestTopicConstants(unittest.TestCase):
    """Verify the module-level constants are set correctly."""

    def test_prefix_value(self) -> None:
        self.assertEqual(TOPIC_PREFIX, "cobots_")

    def test_random_length_value(self) -> None:
        self.assertEqual(TOPIC_RANDOM_LENGTH, 30)

    def test_alphabet_contains_uppercase(self) -> None:
        for c in string.ascii_uppercase:
            self.assertIn(c, TOPIC_ALPHABET)

    def test_alphabet_contains_lowercase(self) -> None:
        for c in string.ascii_lowercase:
            self.assertIn(c, TOPIC_ALPHABET)

    def test_alphabet_contains_digits(self) -> None:
        for c in string.digits:
            self.assertIn(c, TOPIC_ALPHABET)

    def test_alphabet_only_alphanumeric(self) -> None:
        """The alphabet must contain only alphanumeric characters."""
        allowed = set(string.ascii_letters + string.digits)
        for c in TOPIC_ALPHABET:
            self.assertIn(c, allowed)


if __name__ == "__main__":
    unittest.main()
