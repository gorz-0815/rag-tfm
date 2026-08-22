"""CLI entry point: python -m src.ask "<question>" [manual_path] [--full-doc | --no-context]"""

import argparse
from pathlib import Path

from src import tracing
from src.query import ask_full_doc, ask_no_context, ask_rag


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask a question about the ingested manual.")
    parser.add_argument("question", help="The question to ask")
    parser.add_argument(
        "manual_path",
        nargs="?",
        type=Path,
        help="Path to the manual (required unless --no-context)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--no-context",
        action="store_true",
        help="Skip retrieval; ask Claude directly with no manual content at all (baseline mode)",
    )
    mode.add_argument(
        "--full-doc",
        action="store_true",
        help="Skip retrieval; send the manual's full text as context instead of top-k chunks",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    tracing.init_tracing()

    if args.no_context:
        mode = "no_context"
    elif not args.manual_path:
        parser.error("manual_path is required unless --no-context is given")
        return
    elif args.full_doc:
        mode = "full_doc"
    else:
        mode = "rag"

    with tracing.traced_span(f"ask_{mode}", question=args.question) as span:
        if mode == "no_context":
            result = ask_no_context(args.question)
        elif mode == "full_doc":
            result = ask_full_doc(args.question, args.manual_path)
        else:
            result = ask_rag(args.question, args.manual_path)

        if span is not None:
            span.update(output=result["answer"], metadata={"sources": result["sources"]})

    print(result["answer"])
    if result["sources"]:
        print("\nSources: " + ", ".join(result["sources"]))

    tracing.flush_tracing()


if __name__ == "__main__":
    main()
