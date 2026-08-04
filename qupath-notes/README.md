# QuPath — Working Notes

*Everything learned hands-on. Upload this into a new chat so nothing is re-derived.*

---

## What was actually done (TCGA-56-8308, LUSC slide)

```
1. slide opened locally in QuPath (.svs from GDC)
2. painted training examples for 7 classes
3. trained a PIXEL CLASSIFIER (Random Trees)
4. Create objects → converted the pixel map into polygons
5. exported all objects as GeoJSON via Groovy script
6. verified in Colab: coordinates align, tissue is correct
```

**Classifier settings used:**
```
Classifier    Random trees (RTrees)
Resolution    Moderate (2.02 µm/px)
Features      Default multiscale features 2D
Output        Classification
Region        Any annotation ROI
```

**Classes painted:** Tumor, Tumor 1, Normal, RBC, RBCs, Stroma, Lymphid Tissue

---

## Create objects — the dialog settings that worked

```
Minimum object size        5000    drops misclassified specks
Minimum hole size          1000    fills tiny internal gaps
Split objects              OFF     ← ON gives dozens of fragments
Delete existing objects    OFF     ← don't wipe annotations
Ignored classes            OFF
New object type            Annotation   ← NOT Detection (annotations export cleanly)
```

**Which "Create objects" scope to pick:**
```
All image          entire slide incl. background — slow, not wanted
Current selection  only the selected region — CAUSE OF THE 1-OBJECT EXPORT BUG
All annotations    ← this one
```

---

## Export — the script that works

Menu route is fragile (see gotchas). Use `Automate → Script editor`:

```groovy
def annotations = getAnnotationObjects()
println "Found ${annotations.size()} objects:"
annotations.each { println "  - " + (it.getPathClass() ?: "unclassified") }

def path = System.getProperty("user.home") + "/regions_all.geojson"
exportObjectsToGeoJson(annotations, path, "FEATURE_COLLECTION")
println "SAVED: " + path
```

The `Found N objects` printout is the point — it tells you *before* uploading whether
all classes were caught. File is written immediately; no separate save step.

**Windows output path:** `C:\Users\<user>\regions_all.geojson`

---

## Gotchas hit (and fixes)

| Problem | Cause | Fix |
|---|---|---|
| Export gave only **1 object** | an object was selected → exported "selected only" | `Edit → Select → Deselect all` first, or use the script |
| Groovy error on `PROJECT_BASE_DIR` | slide opened outside a QuPath *Project* | use `System.getProperty("user.home")` instead |
| 199 fragments instead of ~7 regions | classifier output is naturally patchy | fine — merge by class downstream (`unary_union`) |
| `Automate` menu confusion | several similar entries | it's **Script editor** (not Script interpreter / Shared / User script) |

---

## The coordinate finding (important, verified)

```
QuPath exports in FULL-RESOLUTION pixel space
   = the same space openslide reads at level 0
   → coordinates line up directly, NO conversion needed
```

Verified empirically: exported coords fell inside 80,576 × 73,086, and cropping
each region's centroid returned the expected tissue.

**But still verify every time.** Misaligned coordinate spaces fail *silently* —
wrong tissue, no error message. Always crop-and-look before trusting a run.

---

## Merging fragments in Colab (the join)

```python
import json
from shapely.geometry import shape
from shapely.ops import unary_union
from collections import defaultdict

d = json.load(open("regions_all.geojson"))
feats = d['features'] if isinstance(d, dict) else d
by_class = defaultdict(list)
for f in feats:
    p = f.get('properties', {})
    c = p.get('classification', {})
    name = (c.get('name') if isinstance(c, dict) else None) or p.get('name') or 'unclassified'
    by_class[name].append(shape(f['geometry']).buffer(0))

regions = {k: unary_union(v) for k, v in by_class.items()}
```

`.buffer(0)` repairs self-intersecting polygons. `unary_union` merges overlaps —
**note:** merged area is smaller than the naive sum of polygon areas, because
overlaps stop being double-counted. The merged number is the correct one.

**Tile selection inside a region:** point-in-polygon on the tile centre.

```python
if not poly.contains(Point(x + TILE//2, y + TILE//2)):
    continue
```

---

## Quantification: what QuPath can actually measure

Not used yet, but available and relevant:

```
Area per class            from the classifier — how much tumour / stroma / normal
Cell detection            nuclei count, size, shape, staining intensity per cell
Cell classification       label detected cells by type
Measurement maps          colour every tile/cell by a score → overlay on tissue
Add measurements          attach numeric features to objects, export as CSV
Positive cell detection   for IHC-style scoring
```

**Why this matters for the foundation-model work:**
QuPath gives *interpretable, human-readable* numbers (cell counts, areas,
stain intensity) — the opposite of a 1,536-number embedding. That makes it the
natural instrument for **verifying** what a foundation model claims:

```
model says          →  "this region is X"
QuPath quantifies   →  cellularity, composition, stain stats
you adjudicate      →  does the tissue support the claim?
```

That's the role reversal agreed for Project 4: the foundation model is under test,
QuPath (and the human eye) verify.

---

## Honest constraint to carry forward

The user is a biomedical scientist with a histotechnology background —
**not a diagnostic pathologist.**

```
✓ can defend:  tumour / stroma / blood / normal / artefact  (recognition)
✗ cannot:      well vs moderately vs poorly differentiated  (grading)
```

The "Tumor vs Tumor 1" split was a *grade* call (poorly vs moderately) and was
therefore set aside — regions kept, grade labels dropped. Correct design:
**supply regions you can defend seeing; let the model do the grading.**
Testing whether a model's grade is *stable* only requires seeing that two
regions differ — not knowing what grade they are.

---

## Files

```
regions_all.geojson    199 objects, all classes   (on the laptop)
```

Merged areas from that export (Colab, unary_union):
```
Tumor      53,400,248 px²
Tumor 1     9,358,107 px²
Normal     13,456,274 px²
```
≈ 730 / 54 / 61 tiles at 512 px — note the **13:1 imbalance**; any region
comparison must cap all regions at the same tile count or sample size becomes
the confound.
