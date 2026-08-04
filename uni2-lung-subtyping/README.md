# UNI2 Lung-Cancer Subtyping

Adenocarcinoma vs squamous, from pre-computed UNI2-h embeddings.
Baseline (mean-pool + logistic regression) vs attention-MIL; both ~0.95 AUROC on
patient-level splits. The attention model's real value is **interpretability** —
its focus maps onto the class-defining morphology.

**Read [`WRITEUP.md`](./WRITEUP.md) for the full story, method, and glossary.**

Figures: attention heatmaps and top-attention crops mapped to real H&E.

Slides: TCGA-LUAD / TCGA-LUSC via the GDC portal. Model: UNI2-h (gated, Mahmood Lab).
Not clinical. Code AI-implemented under the author's direction; results verified
against ground truth.
