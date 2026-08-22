"""Mocked tests for src.ask.main(): verify the tracing span records the
answer/sources as output, and that a no-op span (tracing unconfigured)
doesn't break the CLI. Doesn't call the real Anthropic API or LlamaIndex -
src.ask.ask_no_context/ask_rag/ask_full_doc are monkeypatched directly.
"""

from contextlib import nullcontext

from src import ask


class FakeSpan:
    def __init__(self):
        self.updates = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def update(self, **kwargs):
        self.updates.append(kwargs)


def test_main_records_answer_and_sources_as_span_output(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["ask", "irrelevant question", "--no-context"])
    monkeypatch.setattr(ask.tracing, "init_tracing", lambda: None)
    monkeypatch.setattr(ask.tracing, "flush_tracing", lambda: None)

    fake_span = FakeSpan()
    monkeypatch.setattr(ask.tracing, "traced_span", lambda *a, **kw: fake_span)
    monkeypatch.setattr(
        ask, "ask_no_context", lambda q: {"answer": "Paris.", "sources": []}
    )

    ask.main()

    assert capsys.readouterr().out.strip() == "Paris."
    assert fake_span.updates == [{"output": "Paris.", "metadata": {"sources": []}}]


def test_main_works_with_a_noop_span(monkeypatch, capsys):
    """When tracing isn't configured, traced_span returns contextlib.nullcontext(),
    which yields None - main() must not try to call .update() on it."""
    monkeypatch.setattr("sys.argv", ["ask", "irrelevant question", "--no-context"])
    monkeypatch.setattr(ask.tracing, "init_tracing", lambda: None)
    monkeypatch.setattr(ask.tracing, "flush_tracing", lambda: None)
    monkeypatch.setattr(ask.tracing, "traced_span", lambda *a, **kw: nullcontext())
    monkeypatch.setattr(
        ask, "ask_no_context", lambda q: {"answer": "Paris.", "sources": []}
    )

    ask.main()  # must not raise

    assert capsys.readouterr().out.strip() == "Paris."
