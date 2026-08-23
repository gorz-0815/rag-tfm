# Comparative eval: RAG vs. no-context baseline

18 hand-written questions against the ingested manual, each answered under both conditions and scored with Ragas (judge: Claude, embeddings: the local HF model used for retrieval).

## Results

| Metric | No-context baseline | RAG |
|---|---|---|
| Faithfulness | 0.093 | 0.958 |
| Answer relevancy | 0.107 | 0.789 |
| Context precision | n/a | 0.616 |
| Context recall | n/a | 0.889 |

Faithfulness for both conditions is judged against the same manual chunks RAG retrieved for each question - the no-context answer never saw them, so its faithfulness score reflects how much it invented versus what the manual actually says. Context precision/recall only apply where retrieval happened, so they're RAG-only.

## Interpretation

RAG scored 0.958 on faithfulness against the manual's actual content, versus 0.093 for the no-context baseline judged against that same content - the baseline has no access to the manual and answers from general world knowledge, so its faithfulness score demonstrates how often that knowledge diverges from this specific product's documented behavior. On manual-specific questions (exact soak times, cartridge model numbers, safety limits), the no-context condition either declines to answer specifically or invents a plausible-sounding but ungrounded number; the RAG condition answers from the retrieved chunks and can be verified against them. Answer relevancy also gaps (0.107 baseline vs. 0.789 RAG): on manual-specific questions the baseline often hedges or answers a more generic version of the question instead of the one actually asked, which the relevancy metric penalizes independently of faithfulness.
