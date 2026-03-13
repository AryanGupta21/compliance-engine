import re
from functools import lru_cache


@lru_cache(maxsize=512)
def compile_pattern(pattern: str) -> re.Pattern:
    """Compile and cache a regex pattern with IGNORECASE flag."""
    return re.compile(pattern, re.IGNORECASE)
