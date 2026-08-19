"""CLI entry point: python -m src.ask "<question>" [--no-rag]"""

import argparse

from src.query import ask_no_rag, ask_rag


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about the ingested manuals.")
    parser.add_argument("question", help="The question to ask")
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Skip retrieval; ask Claude directly with no manual context (baseline mode)",
    )
    args = parser.parse_args()

    result = ask_no_rag(args.question) if args.no_rag else ask_rag(args.question)

    print(result["answer"])
    if result["sources"]:
        print("\nSources: " + ", ".join(result["sources"]))


if __name__ == "__main__":
    main()
