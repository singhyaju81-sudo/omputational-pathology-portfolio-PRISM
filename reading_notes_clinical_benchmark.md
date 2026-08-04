# Reading 1 — "A clinical benchmark of public self-supervised pathology foundation models"

Campanella et al., **Nature Communications** 16:3640 (2025) — open access
https://www.nature.com/articles/s41467-025-58796-1
Code + live leaderboard: https://github.com/sinai-computational-pathology/SSL_tile_benchmarks

*This is the professional version of Project 4. Read the Results and Discussion; skip the maths.*

---

## What they did

```
22 clinically relevant slide-level tasks
3 health systems (Mount Sinai, MSKCC, Sahlgrenska)
real clinical data — generated in normal hospital operation, not curated
two task types:  disease DETECTION  and  BIOMARKER prediction
```

**Models compared:** CTransPath, UNI, Virchow, Virchow2, Prov-GigaPath,
H-optimus-0, Phikon, Phikon-v2, SP22M, SP85M, + an ImageNet ResNet50 baseline.

**Their pipeline — essentially the one already built for UNI2:**
```
tiles at 20x (0.5 µm/px)
   ↓
frozen foundation model → embeddings
   ↓
Gated MIL Attention aggregator + linear classifier
   ↓
20 Monte-Carlo cross-validation splits, report AUC
```

---

## The findings that matter

**1. On detection, the models are basically tied.**
All DINO/DINOv2-trained models perform comparably (AUC > 0.9 everywhere).
H-optimus-0 and Prov-GigaPath edge ahead, but "the improvement is minimal."
ImageNet-pretrained and CTransPath lag consistently.

→ *When accuracy is saturated, robustness becomes the differentiator.*

**2. Scaling laws do NOT hold in pathology.**
Bigger model ≠ better. Bigger pretraining dataset ≠ better. More compute ≠ better.
A 22M-parameter model performs on par with a 1.1B one on most tasks.

**3. Dataset COMPOSITION is the thing that matters.**
Lung biomarker performance tracked how much lung was in the pretraining data
(Prov-GigaPath ~45% lung; UNI ~10%). Data quality/curation > scale.

→ *A model can look "better" merely because it saw more of that tissue.
   Name this as a confound in any organ-specific comparison.*

**4. Biomarker tasks are much harder than detection**, with a wider spread.
Top 3 on biomarkers: H-optimus-0, Prov-GigaPath, UNI.

**5. Inference cost varies enormously.**
Memory 0.127 GB (SP22M) → 4.6 GB (H-optimus-0).
Throughput 2569 tiles/sec (SP22M) → 75 tiles/sec (H-optimus-0).
UNI is called the best performance-per-resource trade-off for biomarkers.

---

## The two gaps they explicitly admit — Project 4 aims here

> Technical variability (tissue fixation, **staining**, scanning) in the benchmark
> is limited to three institutions.

The leading benchmark **undertests stain/technical variation.** That is the gap.

> Most models are trained at 20x. Whether higher resolution or mixed magnification
> helps is "largely unanswered."

The magnification question is named as open by the benchmarkers themselves.

Also flagged: IHC is largely ignored by these models, and inter-institutional
variability for IHC is much greater than for H&E.

---

## Why this validates the angle

```
field's own conclusion  →  accuracy is saturating;
                           composition + robustness are what's left

your PRISM finding      →  input quality changes the output
your histotech edge     →  stain and artefact variation is your native domain
```

Not a naive angle. The current one.

---

## Useful for framing results honestly

- They deliberately **withheld** their test data to prevent contamination —
  a good instinct to cite when discussing benchmark integrity.
- They note Virchow/Virchow2 were trained on MSKCC slides, so overlap with
  MSKCC-derived tasks can't be excluded. **Models are often trained on TCGA too** —
  so if testing on TCGA, note that a model may have seen those slides in pretraining.
- Everything is reported over 20 repeated splits, not a single run.
