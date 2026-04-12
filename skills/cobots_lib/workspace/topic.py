"""
topic.py - Random ntfy topic generation for cobots workspaces.

Provides a helper function to generate a cryptographically secure
random default ntfy topic string. The topic follows the format
``cobots_<30 alphanumeric chars>`` (37 characters total).
"""

import secrets
import string

# Prefix prepended to every generated topic.
TOPIC_PREFIX = "cobots_"

# Number of random alphanumeric characters appended after the prefix.
TOPIC_RANDOM_LENGTH = 30

# Character set used for the random portion of the topic.
TOPIC_ALPHABET = string.ascii_letters + string.digits


def generate_default_topic() -> str:
    """Generates a random default ntfy topic string.

    Returns a string of the form ``cobots_<30 random alphanumeric chars>``
    using the `secrets` module for cryptographically secure randomness.
    The random portion contains uppercase letters, lowercase letters,
    and digits.
    """
    random_part = "".join(
        secrets.choice(TOPIC_ALPHABET)
        for _ in range(TOPIC_RANDOM_LENGTH)
    )
    return TOPIC_PREFIX + random_part
