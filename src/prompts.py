"""Dependency-light prompt/message building, kept free of heavy third-party
imports so it stays unit-testable without installing the full RAG stack.
"""

NO_CONTEXT_MESSAGE = "No relevant content found in the ingested manuals."


def build_context_prompt(question: str, context: str) -> str:
    return (
        "Answer the question using only the context below. "
        "If the context does not contain the answer, say so plainly rather than guessing.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
