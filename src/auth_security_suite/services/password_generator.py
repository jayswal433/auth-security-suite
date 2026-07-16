"""Password combination generator for tiered brute-force search.

Generates candidate passwords in phases (digits → alnum → special).
Phase 3 (special-character required) is active by default.
"""

import itertools
from collections.abc import Iterator

from auth_security_suite.core.settings import Settings


def tiered_combinations(settings: Settings, length: int) -> Iterator[str]:
    """Yield password candidates of a fixed length containing at least one special char.

    Logic:
        - Build the full character pool from digits + letters + special.
        - Use ``itertools.product`` to enumerate every permutation of ``length``.
        - Skip combos that are purely alphanumeric (no special character).

    Phases 1 (digits only) and 2 (letters + digits) can be re-enabled inside
    this function for smaller search spaces — they are commented out in the
    original script.

    Args:
        settings: Application settings providing character sets.
        length: Exact password length to generate.

    Yields:
        String passwords ready to be tested against the login form.
    """
    alnum_set = set(settings.digits + settings.letters)
    full = settings.digits + settings.letters + settings.special

    for combo in itertools.product(full, repeat=length):
        # Only emit passwords that contain at least one special character
        if any(ch not in alnum_set for ch in combo):
            yield "".join(combo)
