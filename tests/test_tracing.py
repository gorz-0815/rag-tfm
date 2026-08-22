"""Mocked tests for src.tracing: verify init/flush/span logic without a real
Langfuse client or network calls, matching the mocked style of test_query.py.
"""

import langfuse
from openinference.instrumentation import llama_index as oi_llama_index

from src import config, tracing


def test_init_tracing_is_a_noop_without_credentials(monkeypatch):
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", None)
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", None)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Langfuse client should not be constructed without credentials")

    monkeypatch.setattr(langfuse, "Langfuse", fail_if_called)

    tracing.init_tracing()


def test_init_tracing_constructs_client_and_instruments_once(monkeypatch):
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr(tracing, "_instrumented", False)

    constructed = []
    monkeypatch.setattr(langfuse, "Langfuse", lambda **kwargs: constructed.append(kwargs))

    instrument_calls = []

    class FakeInstrumentor:
        def instrument(self):
            instrument_calls.append(True)

    monkeypatch.setattr(oi_llama_index, "LlamaIndexInstrumentor", FakeInstrumentor)

    tracing.init_tracing()
    tracing.init_tracing()  # second call must not re-instrument

    assert len(constructed) == 2
    assert len(instrument_calls) == 1


def test_flush_tracing_is_a_noop_without_credentials(monkeypatch):
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", None)
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", None)

    def fail_if_called():
        raise AssertionError("get_client should not be touched without credentials")

    monkeypatch.setattr(langfuse, "get_client", fail_if_called)

    tracing.flush_tracing()


def test_flush_tracing_swallows_client_errors(monkeypatch, capsys):
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", "sk-test")

    class FailingClient:
        def flush(self):
            raise RuntimeError("Langfuse unreachable")

    monkeypatch.setattr(langfuse, "get_client", lambda: FailingClient())

    tracing.flush_tracing()  # must not raise

    assert "tracing flush failed" in capsys.readouterr().out


def test_traced_span_is_a_noop_without_credentials(monkeypatch):
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", None)
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", None)

    def fail_if_called():
        raise AssertionError("get_client should not be touched without credentials")

    monkeypatch.setattr(langfuse, "get_client", fail_if_called)

    with tracing.traced_span("extract_manual_text", manual_path="foo.pdf"):
        pass


def test_traced_span_delegates_to_client(monkeypatch):
    monkeypatch.setattr(config, "LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setattr(config, "LANGFUSE_SECRET_KEY", "sk-test")

    calls = []

    class FakeSpan:
        def __init__(self):
            self.updates = []

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def update(self, **kwargs):
            self.updates.append(kwargs)

    class FakeClient:
        def start_as_current_observation(self, **kwargs):
            calls.append(kwargs)
            return FakeSpan()

    monkeypatch.setattr(langfuse, "get_client", lambda: FakeClient())

    with tracing.traced_span("extract_manual_text", manual_path="foo.pdf"):
        pass

    assert calls == [
        {"name": "extract_manual_text", "as_type": "span", "input": {"manual_path": "foo.pdf"}}
    ]
