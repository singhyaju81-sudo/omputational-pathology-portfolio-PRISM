# The UNI2 Project

*Revision document. Read start to finish, or jump to a section.*

---

## Numbers at a glance

**Main run**
```
300 slides        150 LUAD + 150 LUSC     (TCGA)
~225 train        ~75 test                (77 in the recorded run)
Split by patient  10 repeated splits

Baseline          AUROC 0.95 ± 0.02
Attention-MIL     AUROC ~0.95
```

**Earlier, smaller run**
```
80 slides         40 LUAD + 40 LUSC
~60 train         ≈30 LUAD + 30 LUSC
20 test           10 LUAD + 10 LUSC

Baseline          AUROC ~0.95
Attention-MIL     AUROC ~0.90    ← trailed
```

**Attention model training**
```
20 epochs
loss 0.69 → 0.017
```

Baseline has no epochs and no loss. It is fitted in one step.

**Per tile**
```
1 vector, 1,536 numbers   (UNI2-h)
```

---

## The aim

Two questions.

**The surface question:**

> Can a computer tell two lung cancers apart from tissue images alone?

Adenocarcinoma (LUAD) vs squamous cell carcinoma (LUSC).

A pathologist tells these apart by eye. They behave differently and are treated differently.

**The real question:**

> Is the model right for the *right reason*?

A model can be accurate by latching onto something irrelevant.

A staining quirk. A scanner signature. An artefact.

Then it fails silently on the next slide.

So the project had two halves:

```
1. Build a model that separates LUAD from LUSC
2. Check what it actually looked at
```

Half 2 is the point.

---

## Why embeddings, not images

The obvious approach is to feed slides into a model.

That hits a wall immediately.

```
One whole-slide image
= ~100,000 pixels across
= gigabytes
```

Too big. And I had no hardware for thousands of them.

**The unlock:**

Someone had already run every TCGA slide through a model called **UNI2**.

Each small tile became a short list of numbers. They published the numbers.

So I worked with those instead of images.

```
gigapixel slide  →  ✗  too big
lists of numbers →  ✓  runs on free Colab
```

**Important distinction:**

The embeddings exist because UNI2 was **run over** those slides.

Not because UNI2 was **trained on** them.

A trained, frozen model can describe any slide it's shown — including ones it never saw in training.

---

## The pipeline

```
              300 whole-slide images
              (150 LUAD + 150 LUSC)
                        |
              Tile into patches
              (thousands per slide)
                        |
              UNI2 encoder (frozen)
              1,536 numbers per tile
                        |
            +-----------+-----------+
            |                       |
      Mean-pool               Attention-MIL
   (average all tiles)     (learns tile weights)
            |                       |
   Logistic regression          Classifier
      (the baseline)                |
            |                       |
       AUROC 0.95              AUROC 0.95
                                    |
                            Attention heatmap
                             (where it looked)
                                    |
                             Crop top tiles
                             from real H&E
                                    |
                            Morphology check
                            (glands vs keratin)
```

Everything is shared up to the embeddings.

Then it **forks**.

**Left branch** — the control. Average everything. Fit the simplest model. Get a number.

**Right branch** — costs more. Returns the *same* number.

But the right branch keeps going after the score.

Heatmap → crop the tissue → check the morphology.

The baseline structurally cannot do that.

That is the argument for having built it.

---

## One tile, one vector

The embeddings step is the heart of it. Slow down here.

Take a single tile:

```
256 × 256 pixel image (at 20×)
┌────────────────────┐
│  Tumour cells      │
│  Lymphocytes       │
│  Stroma            │
│  Glands            │
└────────────────────┘
```

That's just pixels.

Pass it through UNI2:

```
[0.73, -1.12, 0.44, ..., 0.18]
        1,536 numbers
```

One tile in. **One** list out.

That list is the **embedding**.

**Read the wording carefully:**

```
✓  one vector, 1,536 numbers long
✗  1,536 vectors
```

1,536 is the **length**. Its "dimensionality."

Different models, different lengths:

| Model | Length |
|---|---|
| UNI2-h (this project) | 1,536 |
| UNI (original) | 1,024 |
| Virchow (PRISM project) | 2,560 |

---

### What do the numbers mean?

Conceptually, each position holds one learned feature:

| Position | Might loosely relate to |
|---|---|
| 1 | nuclear density |
| 2 | nuclear size |
| 3 | lymphocyte abundance |
| 4 | glandular architecture |
| 5 | stromal texture |
| … | … |
| 1,536 | some combination of many patterns |

**The crucial caveat:**

Nobody programmed those meanings in.

UNI2 learned during pretraining which patterns are worth encoding.

So most positions don't map to anything human-nameable. Each is a blend.

You can't open number 47 and find "keratin."

---

### The analogy

To describe a person, you could send a photograph.

Or you could send:

```
Height  = 180 cm
Weight  = 75 kg
Hair    = brown
Eyes    = blue
Age     = 42
```

Five numbers that capture what matters.

UNI2 does the same to a tile. With 1,536 descriptors instead of pixels.

---

### Why not use the image?

```
256 × 256 × 3 = 196,608 pixel values
          ↓
        UNI2
          ↓
      1,536 numbers
```

Roughly **128× compression**.

Keeps what's useful. Discards the rest.

*(Small print: tiles are 256 px, but the model ingests 224 × 224. Doesn't change the idea.)*

---

### Why "vector" and not just "list"?

Because the **order is fixed and position means something**.

Start with two numbers:

```
Person A = [180, 75]     (height, weight)
Person B = [178, 77]
Person C = [155, 50]
```

Draw each as a **point** on a graph. Height on one axis, weight on the other.

Now something useful appears:

```
A and B  →  land close together
C        →  sits far away
```

Distance between points = how similar the people are.

**That's the whole reason for the word.**

A vector is a list of numbers that doubles as a **point in space**.

Your embedding is the same idea with 1,536 axes.

```
Tile = a point in 1,536-dimensional space
```

You can't picture that. Nobody can. The arithmetic doesn't care.

**Why this matters:**

Calling it a vector licenses the maths you did.

```
Baseline averaged 2,000 vectors
   → geometrically: the centre of gravity of a slide's points
   → one point representing the whole slide

Logistic regression drew a boundary
   → literally a flat surface through 1,536-dim space
   → LUAD points one side, LUSC the other
```

You can only do that to things that live in a space.

**And why any of it works at all:**

Similar tiles land near each other.

```
two glandular tiles, different patients  →  nearby points
a glandular tile vs a keratinising tile  →  far apart
```

UNI2's whole job in pretraining was to learn an arrangement where visual similarity becomes **geometric closeness**.

Once that's true, separating LUAD from LUSC = finding a boundary between two clouds of points.

Which is why something as unglamorous as logistic regression hit 0.95.

```
"list of numbers"  →  describes the storage
"vector"           →  describes the geometry
```

The geometry is what made the project possible.

---

### How it scales

Slides had several thousand tiles each.

*(Never counted exactly. Estimated 5,000–15,000, depending on tissue area.)*

The attention model capped each slide's bag at 2,000:

```
Tile 1     →  [1,536 numbers]
Tile 2     →  [1,536 numbers]
...
Tile 2000  →  [1,536 numbers]
```

Per slide:

| | Tiles used | Vectors per slide | Numbers per slide |
|---|---|---|---|
| Baseline | all (est. 5–15k) | **1** (the average) | **1,536** |
| Attention-MIL | capped at **2,000** | **2,000** | **~3.07 million** |

Across all 300 slides:

```
Attention dataset  ≈ 600,000 tiles  ≈ 920 million numbers
Baseline dataset   ≈ 460,800 numbers
```

A ~2,000-fold difference in data volume.

That's why:

```
baseline   → ran instantly on CPU
attention  → needed a GPU and Drive checkpointing
meanpool.npz → tiny
patches/     → not tiny
```

*(Both figures are ceilings. The 2,000 cap means slides with fewer tiles contributed fewer.)*

---

### The point most worth internalising

**My attention model never saw a single pathology image.**

It only ever received vectors. Numbers.

When I cropped the top-attention tiles and saw glands and keratin — I went back to the *slide* for those pixels, using each tile's stored coordinates.

The model was working blind.

So "the model looked at glandular tumour" is a statement about **coordinates and weights**.

Not about the model seeing tissue the way I do.

---

### One honest asymmetry

```
Baseline        → averaged ALL tiles
Attention-MIL   → saw a random 2,000-tile subsample
```

So the two models didn't see quite identical data.

Not fatal. 2,000 tiles is a lot of tissue, and the subsample is a blind random cut — it doesn't bias toward interesting regions.

But if asked *"was the comparison perfectly controlled?"* —

The honest answer is **no**.

The cap was a storage choice on free Colab. Not a scientific one.

---

## Evaluating honestly

I split the 300 slides:

```
~225 train    the model learns from these
~75 test      it never sees these
```

*(77 test slides in the recorded run, roughly balanced between subtypes.)*

**But I split by patient, not by slide.**

Why this matters:

```
One patient can contribute several near-identical slides.

If one trains the model and another tests it —
the model can "recognise" a patient it has already seen.

Score goes up. Nothing was learned.
```

That's called **leakage**.

Splitting by patient means every test patient is genuinely new.

I also ran the split 10 times and averaged. One lucky draw proves nothing.

---

## The results

**On the full 300-slide run:**

```
Baseline        0.95 ± 0.02
Attention-MIL   ~0.95
```

The simple model was **just as good** as the complex one.

Why: the features distinguishing these two cancers are spread across the whole tumour.

Plain averaging already captures the signal. Attention had little to add.

**On the earlier 80-slide run:**

```
Baseline        ~0.95
Attention-MIL   ~0.90    ← trailed
```

This is what made it a real finding rather than a fluke.

With ~60 training slides, the attention model hadn't seen enough examples to show its worth.

Only at 300 slides did it catch up.

```
Complex models are data-hungry.

Little data  → the simple model wins comfortably
More data    → the sophisticated one draws level
```

*(Caveat: with only 20 test slides, the 80-slide numbers are noisy. One slide flipping moves accuracy 5 points. Read it as "the gap closed with more data" — not as an exact decimal.)*

---

## The training details

### Epochs and loss

**Baseline: none.**

Logistic regression is fitted in a single step by scikit-learn.

No iterative training. No loss-per-epoch. Nothing to report.

It's summarised entirely by AUROC and accuracy.

**Attention-MIL: 20 epochs.**

An *epoch* = one full pass over the training slides.

During training the model minimises a *loss* — one number measuring how wrong it is.

```
epoch 1    loss 0.6911
   ...
epoch 20   loss 0.0169
```

That starting value is meaningful:

```
0.69 ≈ ln(2) ≈ pure guessing on a two-class problem
```

So epoch 1 = the model knows nothing.

The steady drop after = it's genuinely learning.

*(These figures are from one specific 300-slide run. The model was retrained several times — after resets, and for the 80- vs 300-slide comparison. I don't have every loss curve, so I quote the run I observed rather than inventing a set.)*

---

### Why 20 epochs?

**20 was a default I chose.** Not a number derived from the data.

Enough passes for a small model on a small dataset. Not so many it wastes time.

The loss curve then confirmed it was reasonable:

```
loss dropped smoothly, then flattened near zero
   ↓
the model had CONVERGED
   ↓
finished learning well before epoch 20
```

**Converged** = further training stops making a meaningful difference. The curve goes flat.

So 20 was safe. If anything slightly more than needed — it would have reached almost the same point by epoch 12–15.

**The rigorous way to choose:**

**Early stopping.** Watch performance on a validation set during training. Stop when it stops improving.

I used a fixed 20 for simplicity. For a more rigorous version, early stopping is what I'd add.

**One honest caveat:**

A training loss falling almost to zero is a mild warning sign.

It can mean the model is starting to **memorise** the training data rather than learn the general pattern. That's overfitting.

Why it's not a worry here: the held-out, patient-level test still gave good AUROC.

Generalisation held up.

---

### Error rate

On the 80-slide run, the test set was **20 slides — 10 LUAD, 10 LUSC**.

The attention model gave this confusion matrix: `[[9 1] [1 9]]`

**First, the general shape.** What each cell *means*:

| | **Model says LUAD** | **Model says LUSC** |
|---|---|---|
| **Truly LUAD** | ✅ correct | ❌ LUAD mistaken for LUSC |
| **Truly LUSC** | ❌ LUSC mistaken for LUAD | ✅ correct |

The **diagonal** (top-left → bottom-right) is the successes.

The other two cells are the two *different kinds* of mistake.

That's the whole idea: instead of one accuracy number, you see **which way** each error went.

**Now the actual result:**

| | **Predicted LUAD** | **Predicted LUSC** | Total |
|---|---|---|---|
| **True LUAD** | **9** ✅ | 1 ❌ | 10 |
| **True LUSC** | 1 ❌ | **9** ✅ | 10 |
| Total | 10 | 10 | **20** |

```
Correct   9 + 9 = 18
Wrong     2 of 20
Accuracy  90%
Error     10%
AUROC     0.95 on that split
```

The errors fall **one in each direction**.

So the model wasn't biased toward calling everything one subtype.

**Why that matters — a contrast:**

| (hypothetical) | **Predicted LUAD** | **Predicted LUSC** | Total |
|---|---|---|---|
| **True LUAD** | 10 ✅ | 0 | 10 |
| **True LUSC** | 2 ❌ | 8 ✅ | 10 |

Also 18 of 20. Also 90% accurate. Identical headline number.

But it never misses a LUAD, and wrongly calls two LUSC cases LUAD.

It **leans toward LUAD**.

Same accuracy. Different bias.

That's why the matrix is worth showing rather than the single number.

---

### Accuracy vs AUROC

Easy to conflate. They're different.

```
Accuracy   fraction correct AFTER rounding the
           probability to yes/no at 0.5

AUROC      how well the model RANKS the two classes
           across all thresholds — ignores the rounding
```

AUROC is the more stable headline.

Accuracy is the more intuitive companion.

I lead with AUROC and quote accuracy alongside.

---

## The interpretability step

This is where the project becomes mine.

The attention model can show **which regions drove its decision**.

```
1. Take the highest-attention tiles
2. Map them back onto the original H&E using their coordinates
3. Look at the actual tissue
```

**What I found:**

| Case | True | Model focused on |
|---|---|---|
| TCGA-MP-A4T6 | LUAD | **gland-forming tumour** |
| TCGA-56-8308 | LUSC | **keratinising nests** |

Those are the exact morphological features used to diagnose each.

The model wasn't guessing.

It was attending to the class-defining tissue.

**That closes the loop the project was built around:**

```
not just "it's accurate"
but     "it's accurate for the right reason"
```

Verified by eye. Against real morphology.

---

## The limits

State these plainly. They're what make the claim credible.

**Interpretability was shown on representative single cases.**

Not quantified across hundreds — including misclassifications, which are often the most revealing.

**Morphology reads are visual.**

"Consistent with." Not a formal diagnostic sign-out.

I'm a biomedical scientist with a histopathology background. Not a diagnostic pathologist.

**Public data, released embeddings, no external validation cohort.**

---

## How the results were validated

Worth being explicit, since I didn't write the code myself.

Nothing rests on trusting the pipeline blindly:

```
The model's predictions   → checked against the real morphology
                            (glands / keratin — visible, independent)

The slide identities      → checked against GDC ground truth

Stability                 → 10 repeated patient-level splits,
                            not one lucky draw
```

**The honest position:**

The results are **well-supported and independently sanity-checked.**

Not **formally code-verified.**

There's a real category of bug that produces plausible-but-wrong results with no error message. A subtle leak. An off-by-one in the split. I can't rule that out by reading the code, because I can't read the code.

What I *can* say: the outputs were checked against things outside the code.

If the pipeline were shuffling labels or leaking data, the morphology wouldn't have lined up with the predictions.

That's the best protection available — and it's the normal division of labour. In a team, an engineer reviews the code. The scientist checks the result makes biological sense.

---

## Glossary

**Whole-slide image (WSI)** — a digitised microscope slide. Gigapixels. Never downloaded here.

**Tile / patch** — a small square cut from a slide. 256 × 256 px at 20×. Thousands per slide.

**Embedding** *(= feature vector = features)* — the *one* list of numbers (1,536 for UNI2-h) describing *one* tile. Not 1,536 vectors — one vector of 1,536 dimensions. Similar tiles get similar numbers.

**Dimensionality** — the length of an embedding. UNI2-h = 1,536. Original UNI = 1,024. Virchow = 2,560. Fixed by the model, not by you.

**Foundation model** — a large model pre-trained on huge data, reusable for many tasks. UNI2 is one. You *use* it; you don't train it.

**Frozen model** — a model you run but never retrain. Which is why its embeddings can be pre-computed once and reused.

**Inference** — running a finished model to get its output. As opposed to *training*, where it learns.

**Tile encoder** — the model that describes one tile (UNI2, Virchow). Never sees the slide.

**Slide encoder** — the model that fuses thousands of tile-vectors into one slide-vector. My mean-pool and attention-MIL are both slide encoders — one crude, one learned.

**Dataset vs baseline** — the *dataset* is the raw material (embeddings + labels). The *baseline* is the simple model trained on it. I built both.

**Baseline** — a deliberately simple model, used as a reference point so a fancier one has something honest to be measured against.

**Mean-pooling** — averaging a slide's tile-embeddings into one vector.

**MIL (multiple instance learning)** — learning when you have a "bag" (slide) of "instances" (tiles) but only a bag-level label.

**Attention** — the model learning to weight informative tiles above the rest. The weights double as a heatmap.

**Weakly-supervised** — one label per whole slide, not region-by-region. The model works out which parts matter.

**Training set / test set** — what the model learns from vs the held-out slides used only to check it.

**Patient-level split** — all of one patient's slides stay on the same side, so the model is always tested on genuinely unseen patients.

**Leakage** — when information from testing sneaks into training and inflates the score. Patient-level splitting prevents it.

**Epoch** — one full pass over the training data. Attention model: 20. Baseline: none.

**Loss** — one number measuring how wrong the model is. Training drives it down. 0.69 → 0.017 here. Only the attention model has one.

**Converged** — further training stops making a meaningful difference. The loss curve flattens.

**Early stopping** — choosing the epoch count properly: watch a validation set, stop when it stops improving. Not used here.

**Overfitting** — memorising quirks of the training data instead of the general pattern. Held-out testing detects it.

**Generalisation** — performing well on genuinely new data.

**AUROC** — 0.5 (random) to 1.0 (perfect). The chance the model ranks a random LUSC above a random LUAD. More stable than accuracy.

**Accuracy / error rate** — fraction right / wrong after rounding at 0.5. 90% / 10% on the 80-slide run.

**Confusion matrix** — rows = truth, columns = prediction. Diagonal = correct. Shows *which way* errors go, which accuracy alone can't.

---

## FAQ

**Why not use the actual slide images?**

Gigapixel-huge. Serious hardware needed. Pre-computed embeddings sidestep it — small number-files instead of enormous images.

**Were the embeddings there because UNI2 was trained on those slides?**

No. A trained, frozen model can produce an embedding for *any* slide by running over it. It needn't have trained on that slide. Someone ran UNI2 over TCGA and released the outputs.

**What's the difference between the dataset and the baseline?**

Dataset = raw material (embeddings + labels). Baseline = the simple model trained on it. I made both.

**How many tiles per slide, and how many vectors per tile?**

One vector per tile, 1,536 numbers long. Raw tiles per slide never counted exactly — estimated 5,000–15,000. Attention model capped each bag at 2,000. Baseline averaged all tiles.

**Did both models see the same data?**

Almost, not exactly. Baseline averaged *all* tiles; attention used a random 2,000-tile subsample. Blind random cut, so no bias toward interesting tissue — but "perfectly controlled?" is honestly no.

**Did the model ever see the tissue images?**

No. Only the embeddings — numbers. When I cropped top-attention tiles and saw glands, I fetched those pixels from the *slide* using stored coordinates. The model was blind.

**Did the model train on all the slides?**

No. Of 300: ~225 train, ~75 test. Judged only on held-out slides. (Split is by patient, so exact counts wobble.)

**Why split by patient rather than randomly?**

One patient can have several near-identical slides. If they appear on both sides, the model cheats by recognising the patient. Patient-level splitting makes every test case genuinely new.

**Why did the simple model do as well as the complex one?**

The distinguishing morphology is spread across the whole tumour, so averaging already captures it. Attention had little to add *in accuracy*.

**If the attention model didn't beat the baseline, why build it?**

Because it shows *where* it looked. That's the "right for the right reason" check. The baseline can't provide it.

**What was the error rate?**

80-slide run: 2 of 20 misclassified. 10% error, 90% accuracy, errors balanced one each way. 300-slide run: more stable, both models ~0.95 AUROC across ~75 test slides.

**What about loss and epochs?**

Attention model only: 20 epochs, loss ~0.69 → ~0.017. The baseline isn't trained in epochs and has no loss curve — fitted in a single step.

**Why 20 epochs specifically?**

A sensible default, not derived from the data. The loss curve confirmed the model had converged well before then. The rigorous way is early stopping; I used a fixed 20 for simplicity.

**Did I write the code myself?**

I directed the analysis and did the interpretation. I used AI tools to implement it. The scarce part — the scientific choices and the tissue judgement — was mine.

---

## The one-paragraph version

> "I tested whether an open foundation model's embeddings — UNI2 — could separate two lung cancers, adenocarcinoma vs squamous cell carcinoma, on 300 TCGA slides. I built a simple baseline and an attention model. Both reached about 0.95 AUROC on patient-level splits, and the simple one was just as good — a reminder that complexity isn't automatically better. Then I mapped the attention model's focus back onto the real tissue and confirmed it was looking at the class-defining morphology: glands for adenocarcinoma, keratinising nests for squamous. So it wasn't just accurate. It was right for the right reason. That verification is the part I think matters most."
