# Comparative eval: RAG vs. full-doc vs. no-context baseline

18 hand-written questions against the ingested manual, each answered under all three modes and scored with Ragas (judge: Claude, embeddings: the local HF model used for retrieval).

## Results

| Metric | No-context baseline | Full-doc | RAG |
|---|---|---|---|
| Faithfulness | 0.076 | 0.968 | 0.975 |
| Answer relevancy | 0.107 | 0.816 | 0.738 |
| Context precision | n/a | n/a | 0.616 |
| Context recall | n/a | n/a | 0.889 |
| Latency (avg, s) | 3.51 | 2.01 | 2.74 |
| Cost per query (avg, $) | 0.00085 | 0.00316 | 0.00208 |

Faithfulness is judged against what each condition was actually given: RAG's retrieved chunks for RAG, the manual's full text for full-doc. The no-context baseline never saw any manual content, so it's judged against RAG's retrieved chunks too - its score reflects how much it invented versus what the manual actually says. Context precision/recall only apply where retrieval happened, so they're RAG-only.

## Interpretation

RAG scored 0.975 on faithfulness against the manual's actual content, versus 0.076 for the no-context baseline judged against that same content - the baseline has no access to the manual and answers from general world knowledge, so its faithfulness score demonstrates how often that knowledge diverges from this specific product's documented behavior. On manual-specific questions (exact soak times, cartridge model numbers, safety limits), the no-context condition either declines to answer specifically or invents a plausible-sounding but ungrounded number; the RAG condition answers from the retrieved chunks and can be verified against them. Answer relevancy also gaps (0.107 baseline vs. 0.738 RAG): on manual-specific questions the baseline often hedges or answers a more generic version of the question instead of the one actually asked, which the relevancy metric penalizes independently of faithfulness. Full-doc's faithfulness (0.968) is on par with RAG's (0.975), each judged against what it was actually given - for this manual's size and this eval's questions, RAG's retrieval isn't losing meaningfully relevant content, so full-doc's larger per-query token cost (see the README's cost/latency section) buys little accuracy here. Wall-clock latency (avg per question, including this process's own retrieval/extraction time, not just the LLM call): 3.51s no-context, 2.74s RAG, 2.01s full-doc - full-doc's much larger input isn't the bottleneck here (prompt input is fast to process regardless of length), so it isn't slower than RAG despite its far larger per-query token spend. The no-context baseline is the slowest of the three despite doing the least work: its answers run roughly 2.6x longer (664 vs. 252 characters on average) since there's no 'answer only from this context, concisely' system prompt constraining it - output generation, not input size, dominates latency here. RAG's own average includes a one-time embedding-model load on the first question (12.2s of it); excluding that startup cost, RAG averages 2.18s per query, on par with full-doc. This is a single run over 18 questions against one small local backend, not a rigorous benchmark - treat it as a directional signal, not a production latency SLA. Per-query cost (from Anthropic's actual reported token usage, at claude-haiku-4-5's published rates): $0.00085 no-context, $0.00208 RAG, $0.00316 full-doc - full-doc costs about 1.5x RAG's per-query price, almost entirely from input tokens (the whole manual, resent on every query, versus a handful of retrieved chunks). This is the actual trade-off full-doc's faithfulness parity with RAG comes at: not accuracy, and not necessarily latency, but dollars - at higher query volume or a larger manual, that gap scales linearly with corpus size for full-doc and stays roughly flat for RAG.
