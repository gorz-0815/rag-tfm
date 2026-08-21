"""CLI entry point: python -m src.ask "<question>" [--no-context | --full-doc MANUAL_PATH]"""

import argparse
from pathlib import Path

from src.query import ask_full_doc, ask_no_context, ask_rag


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about the ingested manual.")
    parser.add_argument("question", help="The question to ask")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--no-context",
        action="store_true",
        help="Skip retrieval; ask Claude directly with no manual content at all (baseline mode)",
    )
    mode.add_argument(
        "--full-doc",
        metavar="MANUAL_PATH",
        type=Path,
        help="Skip retrieval; send this manual's full text as context instead of top-k chunks",
    )
    args = parser.parse_args()

    if args.no_context:
        result = ask_no_context(args.question)
    elif args.full_doc:
        result = ask_full_doc(args.question, args.full_doc)
    else:
        result = ask_rag(args.question)

    print(result["answer"])
    if result["sources"]:
        print("\nSources: " + ", ".join(result["sources"]))


if __name__ == "__main__":
    main()
