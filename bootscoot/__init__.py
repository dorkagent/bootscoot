"""Programmatic search client for copperknob.co.uk."""

from .client import CopperKnobClient, search
from .exceptions import CopperKnobError, CloudflareChallengeError, SearchError
from .parser import parse_search_results

__all__ = [
    "CopperKnobClient",
    "search",
    "parse_search_results",
    "CopperKnobError",
    "CloudflareChallengeError",
    "SearchError",
]

__version__ = "0.1.0"
