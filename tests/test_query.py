"""Mocked tests for src.query: verify RAG/no-RAG orchestration logic
(prompt building, source extraction, no-context short-circuit) without
calling the real Anthropic API or needing chromadb/llama_index installed.

For a real end-to-end call against the Anthropic API, see test_ask_live.py.
"""

from src import query


class FakeLLMResponse:
    def __init__(self, text):
        self._text = text

    def __str__(self):
        return self._text


class FakeLLM:
    def __init__(self, text="mocked answer"):
        self.text = text
        self.prompts_seen = []

    def complete(self, prompt):
        self.prompts_seen.append(prompt)
        return FakeLLMResponse(self.text)


class FakeNode:
    def __init__(self, content, file_name):
        self._content = content
        self.metadata = {"file_name": file_name}

    def get_content(self):
        return self._content


class FakeRetriever:
    def __init__(self, nodes):
        self._nodes = nodes

    def retrieve(self, question):
        return self._nodes


class FakeIndex:
    def __init__(self, nodes):
        self._nodes = nodes

    def as_retriever(self, similarity_top_k):
        return FakeRetriever(self._nodes)


def test_ask_no_rag_returns_llm_answer(monkeypatch):
    fake_llm = FakeLLM("Paris is the capital of France.")
    monkeypatch.setattr(query, "_build_llm", lambda: fake_llm)

    result = query.ask_no_rag("What is the capital of France?")

    assert result == {"answer": "Paris is the capital of France.", "sources": []}
    assert fake_llm.prompts_seen == ["What is the capital of France?"]


def test_ask_rag_with_no_retrieved_nodes_skips_llm_call(monkeypatch):
    monkeypatch.setattr(query, "load_manuals_index", lambda: FakeIndex([]))

    def fail_if_called():
        raise AssertionError("LLM should not be called when no context is retrieved")

    monkeypatch.setattr(query, "_build_llm", fail_if_called)

    result = query.ask_rag("What is the warranty period?")

    assert result == {"answer": query.NO_CONTEXT_MESSAGE, "sources": []}


def test_ask_rag_builds_context_prompt_and_dedupes_sources(monkeypatch):
    nodes = [
        FakeNode("Soak the cartridge for 15 minutes.", "manual-a.pdf"),
        FakeNode("Rinse under running water.", "manual-a.pdf"),
    ]
    fake_llm = FakeLLM("Soak for 15 minutes, then rinse.")

    monkeypatch.setattr(query, "load_manuals_index", lambda: FakeIndex(nodes))
    monkeypatch.setattr(query, "_build_llm", lambda: fake_llm)

    result = query.ask_rag("How do I set up a new filter?")

    assert result["answer"] == "Soak for 15 minutes, then rinse."
    assert result["sources"] == ["manual-a.pdf"]
    assert len(fake_llm.prompts_seen) == 1
    prompt = fake_llm.prompts_seen[0]
    assert "How do I set up a new filter?" in prompt
    assert "Soak the cartridge for 15 minutes." in prompt
    assert "Rinse under running water." in prompt
