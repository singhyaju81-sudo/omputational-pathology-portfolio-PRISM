# PRISM Report-Generation Evaluation

Run PRISM (Paige) on two lung slides — generating the Virchow embeddings myself —
and check every claim against the **signed pathology report**.

**Finding:** reliable where the answer is in the pixels (tumour type, organ);
unreliable, sometimes confidently, where it is not (lobe, laterality, nodal status).
It never signals which is which. A single slide is not a whole case — most apparent
"errors" were a category error on my part, which is itself the point.

**Read [`WRITEUP.md`](./WRITEUP.md)** for the full chronological account.
See also [`CONCEPTS_AND_FAQ.md`](./CONCEPTS_AND_FAQ.md) and [`RESULTS_LOG.md`](./RESULTS_LOG.md).

Slides: TCGA-56-8308 (LUSC), TCGA-MP-A4T6 (LUAD). Models: Virchow + PRISM (gated, Paige).
n = 2 — a case study, not a claim about the model. Not clinical.
