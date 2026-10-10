"""Example: search CopperKnob from another script.

Run:  python examples/basic_search.py "Cowboy Charleston"
"""

import json
import sys

from bootscoot import CopperKnobClient, CloudflareChallengeError


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "Cowboy Charleston"
    try:
        with CopperKnobClient() as client:
            results = client.search(query, max_results=10)
    except CloudflareChallengeError as exc:
        print(f"Blocked by a bot challenge:\n{exc}")
        sys.exit(2)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
