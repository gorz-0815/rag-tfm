"""Mocked tests for src.eval: verify eval-set loading and per-question
condition orchestration, without calling the real Anthropic API or Ragas.

For results-file formatting, see test_eval_report.py.
"""

from src import eval as eval_module


def test_load_eval_qa_returns_question_ground_truth_pairs():
    eval_qa = eval_module.load_eval_qa()

    assert len(eval_qa) >= 15
    for item in eval_qa:
        assert item["question"]
        assert item["ground_truth"]


def test_run_conditions_runs_all_three_conditions_per_question(monkeypatch):
    eval_qa = [{"question": "How long should I soak the cartridge?", "ground_truth": "15 minutes."}]

    fake_usage = {"input_tokens": 100, "output_tokens": 20}

    def fake_ask_rag(question, manual_path):
        return {
            "answer": "Soak for 15 minutes.",
            "sources": ["manual.pdf"],
            "contexts": ["Soak the cartridge for 15 minutes."],
            "usage": fake_usage,
        }

    def fake_ask_full_doc(question, manual_path):
        return {
            "answer": "Soak the cartridge for 15 minutes before use.",
            "sources": ["manual.pdf"],
            "contexts": ["<the whole manual text>"],
            "usage": fake_usage,
        }

    def fake_ask_no_context(question):
        return {"answer": "Usually about 30 minutes.", "sources": [], "usage": fake_usage}

    monkeypatch.setattr(eval_module, "ask_rag", fake_ask_rag)
    monkeypatch.setattr(eval_module, "ask_full_doc", fake_ask_full_doc)
    monkeypatch.setattr(eval_module, "ask_no_context", fake_ask_no_context)

    rows = eval_module.run_conditions(eval_qa, "manual.pdf")

    assert len(rows) == 1
    row = rows[0]
    latencies = {
        key: row.pop(key) for key in ["rag_latency_s", "full_doc_latency_s", "no_context_latency_s"]
    }
    assert row == {
        "question": "How long should I soak the cartridge?",
        "reference": "15 minutes.",
        "rag_answer": "Soak for 15 minutes.",
        "rag_contexts": ["Soak the cartridge for 15 minutes."],
        "rag_usage": fake_usage,
        "full_doc_answer": "Soak the cartridge for 15 minutes before use.",
        "full_doc_contexts": ["<the whole manual text>"],
        "full_doc_usage": fake_usage,
        "no_context_answer": "Usually about 30 minutes.",
        "no_context_usage": fake_usage,
    }
    assert all(latency >= 0 for latency in latencies.values())
