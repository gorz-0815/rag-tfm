# Comparative eval: RAG vs. full-doc vs. no-context baseline

18 hand-written questions against the ingested manual, each answered under all three modes and scored with Ragas (judge: Claude, embeddings: the local HF model used for retrieval).

## Results

| Metric | No-context baseline | Full-doc | RAG |
|---|---|---|---|
| Faithfulness | 0.093 | 0.962 | 0.968 |
| Answer relevancy | 0.107 | 0.817 | 0.791 |
| Context precision | n/a | n/a | 0.616 |
| Context recall | n/a | n/a | 0.889 |

Faithfulness is judged against what each condition was actually given: RAG's retrieved chunks for RAG, the manual's full text for full-doc. The no-context baseline never saw any manual content, so it's judged against RAG's retrieved chunks too - its score reflects how much it invented versus what the manual actually says. Context precision/recall only apply where retrieval happened, so they're RAG-only.

## Interpretation

RAG scored 0.968 on faithfulness against the manual's actual content, versus 0.093 for the no-context baseline judged against that same content - the baseline has no access to the manual and answers from general world knowledge, so its faithfulness score demonstrates how often that knowledge diverges from this specific product's documented behavior. On manual-specific questions (exact soak times, cartridge model numbers, safety limits), the no-context condition either declines to answer specifically or invents a plausible-sounding but ungrounded number; the RAG condition answers from the retrieved chunks and can be verified against them. Answer relevancy also gaps (0.107 baseline vs. 0.791 RAG): on manual-specific questions the baseline often hedges or answers a more generic version of the question instead of the one actually asked, which the relevancy metric penalizes independently of faithfulness. Full-doc's faithfulness (0.962) is on par with RAG's (0.968), each judged against what it was actually given - for this manual's size and this eval's questions, RAG's retrieval isn't losing meaningfully relevant content, so full-doc's larger per-query token cost (see the README's cost/latency section) buys little accuracy here.
