"""Mocked tests for src.eval: verify eval-set loading, per-question condition
orchestration, and results-file formatting, without calling the real
Anthropic API or Ragas (which needs a real judge LLM call to score).
"""

import json

import pandas as pd

from src import eval as eval_module


def test_load_eval_qa_returns_question_ground_truth_pairs():
    eval_qa = eval_module.load_eval_qa()

    assert len(eval_qa) >= 15
    for item in eval_qa:
        assert item["question"]
        assert item["ground_truth"]


def test_run_conditions_runs_all_three_conditions_per_question(monkeypatch):
    eval_qa = [{"question": "How long should I soak the cartridge?", "ground_truth": "15 minutes."}]

    def fake_ask_rag(question, manual_path):
        return {
            "answer": "Soak for 15 minutes.",
            "sources": ["manual.pdf"],
            "contexts": ["Soak the cartridge for 15 minutes."],
        }

    def fake_ask_full_doc(question, manual_path):
        return {
            "answer": "Soak the cartridge for 15 minutes before use.",
            "sources": ["manual.pdf"],
            "contexts": ["<the whole manual text>"],
        }

    def fake_ask_no_context(question):
        return {"answer": "Usually about 30 minutes.", "sources": []}

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
        "full_doc_answer": "Soak the cartridge for 15 minutes before use.",
        "full_doc_contexts": ["<the whole manual text>"],
        "no_context_answer": "Usually about 30 minutes.",
    }
    assert all(latency >= 0 for latency in latencies.values())


def test_write_results_writes_json_and_markdown_with_scores(tmp_path, monkeypatch):
    monkeypatch.setattr(eval_module.config, "RESULTS_DIR", tmp_path)

    rows = [
        {
            "question": "Q1",
            "reference": "R1",
            "rag_answer": "A1",
            "rag_latency_s": 1.2,
            "full_doc_answer": "C1",
            "full_doc_latency_s": 2.5,
            "no_context_answer": "B1",
            "no_context_latency_s": 0.5,
        },
    ]
    scores = {
        "rag": pd.DataFrame(
            [
                {
                    "faithfulness": 0.9,
                    "answer_relevancy": 0.8,
                    "context_precision": 1.0,
                    "context_recall": 1.0,
                }
            ]
        ),
        "full_doc": pd.DataFrame([{"faithfulness": 0.95, "answer_relevancy": 0.85}]),
        "no_context": pd.DataFrame([{"faithfulness": 0.2, "answer_relevancy": 0.75}]),
    }

    eval_module.write_results(rows, scores)

    raw = json.loads((tmp_path / "eval_results.json").read_text(encoding="utf-8"))
    assert raw["rag"][0]["faithfulness"] == 0.9
    assert raw["full_doc"][0]["faithfulness"] == 0.95
    assert raw["no_context"][0]["faithfulness"] == 0.2
    assert raw["latency_s"] == [{"question": "Q1", "rag": 1.2, "full_doc": 2.5, "no_context": 0.5}]

    report = (tmp_path / "eval_results.md").read_text(encoding="utf-8")
    assert "0.9" in report
    assert "0.95" in report
    assert "0.2" in report
    assert "Latency" in report
    assert "Interpretation" in report
