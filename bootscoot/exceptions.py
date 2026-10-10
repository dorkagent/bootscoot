"""Exceptions raised by bootscoot."""


class CopperKnobError(Exception):
    """Base error for the bootscoot package."""


class CloudflareChallengeError(CopperKnobError):
    """Raised when Cloudflare's bot challenge blocks the request.

    The client uses the ``www`` host, which normally serves plain HTTP
    clients without a challenge. If this error appears, Cloudflare's
    policy changed: wait a while and retry; if it persists, the client
    needs updating (e.g. a browser-based fallback).
    """


class SearchError(CopperKnobError):
    """Raised when a search request fails or results cannot be parsed."""
