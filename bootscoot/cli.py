"""Command-line interface.

Run a search straight from the terminal::

    bootscoot "Cowboy Charleston" --max-results 10
    python -m bootscoot "Bailando" --level Beginner --format json
"""

from __future__ import annotations

import argparse
import json
import sys

from .client import CopperKnobClient
from .exceptions import CloudflareChallengeError, SearchError


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bootscoot",
        description="Search copperknob.co.uk line-dance stepsheets from the command line.",
    )
    p.add_argument("query", help="Search text, e.g. \"Cowboy Charleston\"")
    p.add_argument("--level", default="", help="Level filter, e.g. Beginner")
    p.add_argument("--wall", default="", help="Wall count filter, e.g. 4")
    p.add_argument("--lang", default="", help="Stepsheet language filter")
    p.add_argument("--beat-from", default="", help="Minimum beats per minute")
    p.add_argument("--beat-to", default="", help="Maximum beats per minute")
    p.add_argument("--order", default="Date", help="Result ordering (default: Date)")
    p.add_argument(
        "--max-results", type=int, default=20,
        help="Max results to return, follows pagination (default: 20)",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--proxy", default=None,
        help="Proxy server URL, e.g. http://user:pass@host:3128",
    )
    p.add_argument(
        "--base-url", default=None,
        help="Target site base URL (default: the site the parser was built for)",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with CopperKnobClient(proxy=args.proxy, base_url=args.base_url) as client:
            results = client.search(
                args.query,
                level=args.level,
                wall=args.wall,
                lang=args.lang,
                beat_from=args.beat_from,
                beat_to=args.beat_to,
                order=args.order,
                max_results=args.max_results,
            )
    except (CloudflareChallengeError, SearchError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        if not results:
            print("No results.")
            return 0
        for r in results:
            meta = " | ".join(
                str(x) for x in
                [f"{r['count']}ct" if r.get("count") else None,
                 f"{r['walls']}w" if r.get("walls") else None,
                 r.get("level")]
                if x
            )
            byline = " — ".join(x for x in [r.get("choreographer"), r.get("date")] if x)
            print(f"{r['title']}")
            if byline:
                print(f"  {byline}")
            if meta:
                print(f"  {meta}")
            if r.get("music"):
                print(f"  Music: {r['music']}")
            print(f"  {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
