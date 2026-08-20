# Sample questions — AquaFlow 200 manual

A small hand-written question set for exercising `python -m src.ask` against
the synthetic `data/manuals/aquaflow-200-manual.pdf` manual (see its header
comment for provenance: generated for this repo, not a real product).

Run each with and without `--no-rag` to compare grounded vs. baseline answers:

```
python -m src.ask "How long should I soak a new filter cartridge before using it?"
python -m src.ask "How long should I soak a new filter cartridge before using it?" --no-rag
```

## Simple, single-chunk

1. What is the capacity of the AquaFlow 200 pitcher?
2. How long should I soak a new filter cartridge before using it?
3. What temperature range of water can I use with this filter?

## Numeric / precise recall

4. How many liters or months does one filter cartridge last?
5. How long does it take for a full reservoir to filter?

## Requires combining info across sections

6. I just installed a new filter — what should I do before drinking the water?
7. The water is leaking from the base and tastes like plastic — what should I check?

## Safety / policy nuance

8. Can I use this filter during a boil-water advisory?
9. Is the pitcher dishwasher safe?

## Out-of-scope (should surface "no relevant context", and expose no-RAG hallucination)

10. What's the warranty period for the AquaFlow 200?
11. How do I descale a coffee maker?
