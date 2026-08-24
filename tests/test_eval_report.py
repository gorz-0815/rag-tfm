"""Mocked tests for src.eval_report: verify results-file formatting from
rows + Ragas scores, without calling the real Anthropic API or Ragas.
"""

import json

import pandas as pd

from src import eval_report


def test_build_row_flattens_three_ask_results_and_timings():
    rag_result = {"answer": "A1", "contexts": ["ctx-a"], "usage": {"input_tokens": 1}}
    full_doc_result = {"answer": "C1", "contexts": ["ctx-c"], "usage": {"input_tokens": 2}}
    no_context_result = {"answer": "B1", "contexts": [], "usage": {"input_tokens": 3}}

    row = eval_report.build_row(
        "Q1", "R1", rag_result, 1.2, full_doc_result, 2.5, no_context_result, 0.5
    )

    assert row == {
        "question": "Q1",
        "reference": "R1",
        "rag_answer": "A1",
        "rag_contexts": ["ctx-a"],
        "rag_latency_s": 1.2,
        "rag_usage": {"input_tokens": 1},
        "full_doc_answer": "C1",
        "full_doc_contexts": ["ctx-c"],
        "full_doc_latency_s": 2.5,
        "full_doc_usage": {"input_tokens": 2},
        "no_context_answer": "B1",
        "no_context_latency_s": 0.5,
        "no_context_usage": {"input_tokens": 3},
    }


def test_write_results_writes_json_and_markdown_with_scores(tmp_path, monkeypatch):
    monkeypatch.setattr(eval_report.config, "RESULTS_DIR", tmp_path)

    rag_usage = {"input_tokens": 200, "output_tokens": 50}
    full_doc_usage = {"input_tokens": 3000, "output_tokens": 55}
    no_context_usage = {"input_tokens": 15, "output_tokens": 120}
    rows = [
        {
            "question": "Q1",
            "reference": "R1",
            "rag_answer": "A1",
            "rag_latency_s": 1.2,
            "rag_usage": rag_usage,
            "full_doc_answer": "C1",
            "full_doc_latency_s": 2.5,
            "full_doc_usage": full_doc_usage,
            "no_context_answer": "B1",
            "no_context_latency_s": 0.5,
            "no_context_usage": no_context_usage,
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

    eval_report.write_results(rows, scores)

    raw = json.loads((tmp_path / "eval_results.json").read_text(encoding="utf-8"))
    assert raw["rag"][0]["faithfulness"] == 0.9
    assert raw["full_doc"][0]["faithfulness"] == 0.95
    assert raw["no_context"][0]["faithfulness"] == 0.2
    assert raw["latency_s"] == [{"question": "Q1", "rag": 1.2, "full_doc": 2.5, "no_context": 0.5}]
    assert raw["cost_usd"] == [
        {
            "question": "Q1",
            "rag": eval_report._cost_usd(rag_usage),
            "full_doc": eval_report._cost_usd(full_doc_usage),
            "no_context": eval_report._cost_usd(no_context_usage),
        }
    ]
    assert raw["token_usage"][0]["rag"] == rag_usage
    assert raw["token_usage"][0]["full_doc"] == full_doc_usage

    report = (tmp_path / "eval_results.md").read_text(encoding="utf-8")
    assert "0.9" in report
    assert "0.95" in report
    assert "0.2" in report
    assert "Latency" in report
    assert "Cost per query" in report
    assert "Input tokens" in report
    assert "Output tokens" in report
    assert "Interpretation" in report
