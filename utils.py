"""A few misc utilities.
"""

import re
from typing import cast


def increment_name(name: str) -> str:
    """If ending with an integer, increment and return.
    Otherwise append 1.
    """
    try:
        m = cast(re.Match, re.compile(r"(.*)(\d+)$").match(name))
        name, n = m.group(1), int(m.group(2))
    except:
        n = 0
    return name + str(n + 1)
