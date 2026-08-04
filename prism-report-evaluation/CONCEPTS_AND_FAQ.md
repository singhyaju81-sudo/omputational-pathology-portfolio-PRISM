# PRISM Project — Concepts, What We Did & Why, and FAQ

*A self-contained reference for the PRISM (multimodal vision-language pathology) project, written so you can revisit later and re-grasp every idea. Mirrors the UNI2 master document. Read Part 1 for the story, Part 2 for the step-by-step reasoning, Part 3 for new terms, Part 4 for the FAQ.*

**One-line summary:** We used **PRISM** (a vision-language foundation model built on **Virchow**) to generate free-text pathology reports and zero-shot cancer-subtype calls for whole-slide images, then verified those outputs against ground truth — and showed that *input tile quality* strongly affects the report.

---

# PART 1 — THE BIG PICTURE

## How PRISM differs from the UNI2 project
- **UNI2 project:** numbers in → label out. You turned tiles into embeddings and trained your own classifier (LUAD vs LUSC).
- **PRISM project:** slide in → *text* out. PRISM aggregates tile embeddings itself and **generates language** — a written report, plus zero-shot classification by comparing the slide to *text prompts*. No training on our part.

PRISM is "one layer up": it does the aggregation-and-reasoning step you built by hand in UNI2, and adds a language model on top.

## The pipeline (what feeds what)
```
Raw slide ─► tiles ─► VIRCHOW (tile encoder) ─► tile embeddings [N, 2560]
        ─► PRISM (Perceiver aggregator) ─► slide representation
        ─► PRISM text decoder (BioGPT) ─► written report
        └► PRISM zero-shot (compare slide embedding to text prompts) ─► subtype call
```
- **Virchow** = the tile encoder (like UNI2, but its embeddings are 2,560-dim and are what PRISM expects).
- **PRISM** = aggregator + language model that turns the tile embeddings into text.

## Two phases we did
- **Phase 1 (easy):** used PRISM's *bundled example* Virchow embeddings (a breast slide) to run the whole pipeline with no Virchow step — proved PRISM works and produced a real report.
- **Phase 2 (hard):** generated Virchow embeddings *ourselves* from a raw lung slide (TCGA-56-8308, known LUSC), then fed them to PRISM. This is the full pipeline.
- **Option B:** re-ran Phase 2 with a *better tissue filter* (reject blood/debris) and whole-slide sampling, to test whether cleaner input fixed an error.

## Headline results
| | Diagnosis | Zero-shot | Site claim | Verdict |
|---|---|---|---|---|
| Phase 1 (breast, provided) | invasive ductal carcinoma | 99.87% ductal | breast | Core dx correct; grade/feature unverifiable |
| Phase 2 messy (1,500 blood-heavy tiles) | keratinizing SCC | 99.98% squamous | **"lymph node"** (WRONG) | Dx correct; site error; details unverifiable |
| Option B clean (5,355 filtered tiles) | poorly diff. SCC | 99.95% squamous | **"left lower lobe lung"** (CORRECT) | Site error FIXED by cleaner input |

**Core finding:** PRISM got the diagnosis right every time, but produced confident *errors and embellishments* in the surrounding detail — and cleaning up the input tiles fixed the anatomical-site error. So preprocessing quality materially changes the report.

---

# PART 2 — WHAT WE DID, STEP BY STEP, AND WHY

1. **Set up a gated, GPU environment.** PRISM and Virchow are gated (institutional-email approval) and require a GPU with pinned library versions (transformers ~4.53, torch 2.3–2.8). *Why the pinning:* PRISM loads custom model code that breaks on wrong versions — the torch/torchvision mismatch caused repeated `nms`/import errors until we pinned matching versions and restarted.

2. **Phase 1 — ran PRISM on provided embeddings.** Downloaded the bundled `.pth` of Virchow tile embeddings (~12,000 tiles, breast), built the slide representation, generated a report, and did zero-shot ductal-vs-lobular. *Why:* to prove the whole PRISM chain works before tackling the hard Virchow step. It correctly called invasive ductal carcinoma (matching GDC ground truth).

3. **Phase 2 — made our own Virchow embeddings.** Loaded Virchow, confirmed it outputs the 2,560-dim tile embedding PRISM expects (class token 1,280 + mean of patch tokens 1,280, concatenated), then tiled a raw lung slide, filtered background, and embedded ~1,500 tiles. *Why concatenate class + mean-patch tokens:* that specific 2,560 format is what PRISM was trained to consume.

4. **First result + verification.** PRISM correctly called squamous, but the report said "…in lymph node." We checked ground truth (GDC): TCGA-LUSC, barcode -01Z = primary lung tumour → so "lymph node" is a **site error**. *Why verify:* a model agreeing with itself (report + zero-shot) isn't proof; only external ground truth is.

5. **Diagnosed the likely cause.** Reviewing the 1,500 input tiles showed they were **blood-heavy and top-biased** (the cap took the first 1,500 tiles from the top of the slide, and the filter admitted red-blood-cell fields). Hypothesis: poor input caused the site error.

6. **Option B — engineered a better filter and re-ran.** Built a colour-based tissue filter (reject tiles dominated by red = blood; require blue/purple = nuclei), set the blood threshold to 0.20 *deliberately* so genuinely vascular tumour tiles are kept and only blood-*dominated* tiles rejected. Sampled the **whole slide** (not top-biased), embedded with a **resumable, Drive-checkpointed** pipeline (saves every 200 tiles → a Colab timeout costs seconds). Got **5,355 clean tiles**.

7. **Confirmed the fix.** On clean input, the report changed "in lymph node" → "in **left lower lobe lung**" (correct and specific), while the diagnosis stayed squamous. *Conclusion:* the site error was preprocessing-driven and fixable. The differentiation description also shifted (moderate→poor, "keratinizing" dropped), and reviewing the clean tiles suggested the tumour is predominantly solid/non-keratinizing — so the clean run may be *more* representative.

---

# PART 3 — NEW TERMS (plain English)

**Multimodal AI** — a model that works across more than one *type* of data at once. PRISM is image + text (it reads slide features and writes/compares language). Contrast with UNI2, which was image-only.

**Vision-language model (VLM)** — a model trained on paired images and text, so it can connect what it "sees" to words. This is what lets PRISM generate reports and do zero-shot classification from text prompts.

**Foundation model (recap)** — a large model pre-trained on huge data, reused for many tasks. Virchow and PRISM are foundation models; you use them, you don't train them.

**Virchow** — the *tile encoder* PRISM is built on (like UNI2). Turns each tile into a 2,560-number embedding. Gated.

**PRISM** — the *slide-level* multimodal model: aggregates Virchow tile embeddings into one slide representation and generates text / does zero-shot. Gated. ~558M parameters.

**Tile encoder vs slide model** — two levels. The *tile encoder* (Virchow/UNI2) describes small patches. The *slide model* (PRISM) combines all patches into a whole-slide understanding. Your UNI2 attention model was a simple slide model; PRISM is a powerful pretrained one.

**Class token / patch tokens** — a vision transformer outputs one summary vector (the "class token") plus one vector per sub-region ("patch tokens"). PRISM wants each tile as [class token] + [mean of patch tokens] = 2,560 numbers.

**Report generation (captioning)** — the model writes free text describing the slide, produced word-by-word by a text decoder (PRISM uses **BioGPT**, a biomedical language model).

**Beam search** (`num_beams=5`) — a text-generation method that explores several candidate phrasings and keeps the best, giving more coherent output than picking the single most likely next word.

**do_sample=False** — makes generation deterministic (same input → same report every time), rather than randomly sampling wording.

**Zero-shot classification** — classifying with *no training* by comparing the slide's embedding to the *text* of candidate labels (e.g. "squamous cell carcinoma" vs "adenocarcinoma"). The higher-scoring prompt is the call. This is a VLM superpower and a big contrast with the trained classifier in your UNI2 project.

**Prompt (pos/neg)** — the text descriptions you give zero-shot to compare against (positive vs negative class).

**Perceiver** — the architecture PRISM uses to aggregate a variable number of tiles into a fixed-size slide representation (its version of your attention-pooling step).

**Tokenize / untokenize** — converting text to the numbers a language model uses, and back. `untokenize` turns PRISM's numeric output into readable English.

**Autocast / mixed precision (float16) / inference_mode** — run the model efficiently on the GPU in half-precision, without tracking gradients (we're using it, not training). Just efficiency wrappers.

**Gated repo / institutional email** — a model requiring approval to download; Virchow/PRISM need an institutional-email HuggingFace account.

**Checkpointing / resumable pipeline** — saving progress to disk (Drive) periodically so a crash/timeout resumes instead of restarting. Our fix for Colab resets.

**GDC portal** — public source of TCGA raw slides and the ground-truth diagnosis fields we verified against.

**Tissue/quality filter** — the rule deciding which tiles to keep. Ours used colour: reject red-dominated (blood), require blue/purple (nuclei). The key lever in Option B.

**Perineural / lymphovascular invasion** — pathology findings PRISM asserted; not recorded in TCGA's structured fields, hence "unverifiable" here.

---

# PART 4 — FAQ (the questions you asked, preserved)

**Were the TCGA embeddings pre-computed because the model was *trained* on those slides?**
No. A trained, frozen model can produce embeddings for *any* slide by *running over* it (inference) — it need not have trained on that slide. The embeddings existed because someone ran the model over TCGA and released the outputs, not because of training.

**Does PRISM take UNI2 embeddings?**
No — PRISM takes **Virchow** embeddings (2,560-dim), a different encoder. That's why Phase 2 required running Virchow ourselves rather than reusing your UNI2 features.

**What do P(LUSC)=1.000 / 0.000 mean?**
Probabilities from the zero-shot comparison. 1.000 = certain squamous; 0.000 = certain not-squamous (i.e. adeno). Softmax pushes values to extremes, so treat high confidence as an output to *verify*, not as truth.

**How did we check the ground truth?**
The GDC case page / metadata: `project_id` (TCGA-LUSC = lung squamous), `primary_diagnosis`, and the barcode (`-01Z` = primary solid tumour, not a lymph node). External record, not the model vouching for itself.

**Could the blood be real (vascular tumour), not artefact?**
Yes — tumours can be vascular/haemorrhagic, so blood isn't always artefact. But either way, tiles *dominated* by blood are poor input (little epithelium to characterise). So we reject blood-*dominated* tiles (threshold 0.20) while keeping tumour tiles that merely contain some blood. That's why we chose 0.20, not a stricter cut.

**Why did "keratinizing" disappear on the clean run?**
Most likely the keratinizing focus was over-represented in the biased top-of-slide messy sample and got "averaged out" in the larger, whole-slide clean sample — and reviewing the clean tiles suggests the tumour is predominantly non-keratinizing/poorly-differentiated. It's also biologically consistent (poorly differentiated SCC often doesn't keratinize). Can't be proven without full-slide review; PRISM gives no per-word evidence.

**Can we see which tiles PRISM "looked at" for the report?**
No. Unlike your UNI2 attention model, PRISM does **not** expose per-tile importance for the report — it generates from the whole aggregated representation. We can view the tiles we *fed* it, but not an attention attribution. (A real limitation worth noting.)

**How many tiles / what % of the slide did we analyse?**
Option B embedded **5,355** tiles ≈ **24% of the full slide grid** (~22,300 positions), and effectively the *majority of diagnostic-quality tissue* (the filter rejected ~70% as background/blood/debris). Exact "% of tissue" needs a separate count of tissue-vs-background tiles.

**Would doing all ~23,000 tiles need more memory/compute?**
Memory: no real problem (each embedding ~10KB; 23k ≈ 230MB; tiles processed one at a time). Compute/time: yes, ~4× longer, and most extra tiles are background glass — wasted compute. And it would re-introduce the blood/debris we removed, likely *worsening* the report. More tiles ≠ better; *cleaner* tiles is what helped.

**Is this a study or a case study?**
A **case study (n=1 own slide** + 1 provided example). Compelling and well-verified, but not a general claim about PRISM. More slides (e.g. the LUAD case) would strengthen it toward a pattern.

**Why did the Colab session keep dying?**
Free Colab times out on inactivity and wipes variables *and* installed packages. PRISM/Virchow are heavy (big models, long installs), so recovery was slow. Fix: checkpoint to Drive + save results the moment you get them (and, if doing lots of this, Colab Pro).

---

# PART 5 — HOW TO TALK ABOUT IT (one paragraph)

> "I ran PRISM — a vision-language pathology foundation model built on Virchow — end to end, including generating the Virchow tile embeddings myself from a raw lung slide. PRISM correctly identified squamous cell carcinoma zero-shot, but its generated report confidently placed the tumour 'in lymph node' — a lung primary. I hypothesised the error came from poor input (a blood-heavy, top-biased tile sample), built a colour-based tissue filter to feed it cleaner, whole-slide tiles, and re-ran: the site corrected to 'left lower lobe lung'. So the core diagnosis was robust, but the surrounding detail was sensitive to input quality and partly unverifiable — which is exactly why human oversight matters for generative pathology reports."

---

*Companion files: `PRISM_results_log.md` (the verified results), the tile-grid figures, and this concepts/FAQ document.*
