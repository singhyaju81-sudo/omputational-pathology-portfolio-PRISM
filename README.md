# Computational Pathology — Portfolio

Hands-on projects exploring how AI foundation models behave on real histopathology,
built by a biomedical scientist with a histotechnology background. The through-line
is **evaluation**: not just running these models, but checking — against ground
truth and against the tissue — where they are reliable and where they are not.

> **How this was built, stated plainly.** I am a biomedical scientist with a
> histotechnology and normal-histology background — **not a diagnostic pathologist,
> and not a programmer.** I designed these studies, made the scientific choices, and
> did the tissue interpretation. The code was written with AI coding tools under my
> direction, and results were verified against independent ground truth rather than
> against a model's own confidence. Each project states its own limits.

---

## Projects

### 1. [UNI2 lung-cancer subtyping](./uni2-lung-subtyping/)
Classify TCGA lung slides as adenocarcinoma vs squamous using pre-computed **UNI2-h**
embeddings. A simple baseline (mean-pool + logistic regression) matched a more complex
attention-MIL model (~0.95 AUROC, patient-level splits) — and the attention model's
value turned out to be **interpretability**: its focus mapped back onto the
class-defining morphology (glands for adenocarcinoma, keratinising nests for squamous).
*"Right for the right reason."*

### 2. [PRISM report-generation evaluation](./prism-report-evaluation/)
Run **PRISM** (Paige) — a vision-language model that writes free-text pathology reports
— on two lung slides, generating the **Virchow** tile embeddings myself. PRISM got the
diagnosis and organ right every time, but produced confident errors in the surrounding
detail. Pulling the **actual signed pathology reports** overturned my first conclusions
and produced a sharper finding: the model is reliable where the answer is *in the pixels*
(tumour type, organ) and unreliable — sometimes confidently — where it is not
(lobe, laterality, nodal status), and it never signals which is which.
*"Coherence is not evidence."*

### 3. [QuPath working notes](./qupath-notes/)
Practical, reusable notes for pixel-classifier training, object export, and the
QuPath→Python coordinate handoff — including the gotchas that cost real time.

---

## What is *not* in this repo (and why)

- **No model weights.** UNI2, Virchow and PRISM are gated and licensed for
  non-commercial research; their weights are not redistributable. The code loads them
  from their official sources; you need your own approved access.
- **No whole-slide images.** The slides are public (TCGA, via the GDC portal) but large
  and not mine to host. Slide IDs are given so results can be reproduced.
- **No clinical use.** These are research demonstrations. Nothing here is a diagnosis,
  a medical device, or medical advice.

## Data and models used
- **Slides:** TCGA (LUAD, LUSC) via the [GDC portal](https://portal.gdc.cancer.gov/).
- **Models:** [UNI2-h](https://huggingface.co/MahmoodLab/UNI2-h) (Mahmood Lab),
  [Virchow](https://huggingface.co/paige-ai/Virchow) & PRISM (Paige) — all gated.

## Reading notes
[`assets/reading_notes_clinical_benchmark.md`](./assets/reading_notes_clinical_benchmark.md)
— distilled notes on Campanella et al., *Nature Communications* 2025, the field's
public benchmark of pathology foundation models.

## Licence
Code and writing in this repo: [MIT](./LICENSE). This licence covers **only** the
material in this repository, not the third-party models or datasets referenced.
