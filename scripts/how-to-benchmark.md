# How to benchmark your model

`scripts/benchmark.py` scores your drawing-type predictions against the labelled dataset in `all_data_json/`. You don't need to know how the dataset is organised.

**Requirements:** [uv](https://docs.astral.sh/uv/). There is nothing else to install.

## The task

Each image is a page from a building-drawing set. It contains zero or more drawings of these classes:

| id | class |
|----|-------|
| 0 | `fasade` |
| 1 | `plantegning` |
| 2 | `situasjonskart` |
| 3 | `snitt` |

You can be scored in two ways:

- **Classification** (always): which classes are on the page?
- **Detection** (optional): where are they? This needs bounding boxes.

## Quick start (3 steps)

**1. Generate a template** for the split you want to test (`test` is the default):

```sh
uv run scripts/benchmark.py --template preds.json --split test
```

This writes `preds.json` with every image filename mapped to an empty list.

**2. Fill it in** with your model's output (see formats below).

**3. Run the benchmark:**

```sh
uv run scripts/benchmark.py --predictions preds.json --split test
```

Use the same `--split` for both commands.

## Prediction formats

### Classes only (simplest)

List the classes found on each image. Use `[]` if there are none.

```json
{
  "751473.PDF_page_1.jpg": ["plantegning"],
  "Auglandsstien 9_eksisterende_page_2.jpg": ["fasade", "plantegning"],
  "Eigemyrveien 7B_page_1.jpg": []
}
```

- Class ids work too: `[0, "snitt"]`.
- Repeating a class counts as several instances, for example `["fasade", "fasade"]`. This only affects the "MAE count" column. If you only predict presence, ignore that column.
- Example: [sample_predictions.json](sample_predictions.json)

### With bounding boxes (adds detection metrics)

```json
{
  "751473.PDF_page_1.jpg": [
    {"label": "plantegning", "score": 0.91, "bbox": [267, 1252, 1382, 2081]}
  ]
}
```

- `bbox` is `[x1, y1, x2, y2]` in **pixels** of the original image (top-left and bottom-right corners).
- `score` is optional and defaults to 1.0. Provide it if you have confidences, because AP is more meaningful with them.
- You can mix both forms in one file.
- Example: [sample_predictions_bbox.json](sample_predictions_bbox.json)

## Let the script run your model

Instead of a predictions file, point the script at a Python function:

```python
# my_model.py
def predict(image_path: str) -> list:
    # run your model on the image at image_path
    return ["fasade", "snitt"]    # or a list of {"label", "score", "bbox"} dicts
```

```sh
uv run scripts/benchmark.py --predictor my_model.py:predict --split test
```

`predict` is called once per image. The script reports total and per-image inference time. If your model needs extra packages, run it with `uv run --with <package> scripts/benchmark.py ...`.

## Reading the report

**Classification (image level):**

| metric | meaning |
|--------|---------|
| precision | of the pages where you predicted a class, how many really had it |
| recall | of the pages that have a class, how many you found |
| F1 | the balance of precision and recall |
| support | number of pages that have the class |
| TP / FP / FN | correct, spurious and missed pages |
| micro / macro / weighted F1 | F1 over all pages, averaged per class, or averaged per class by support |
| exact match | pages where you got the *whole* set of classes right |
| hamming acc | share of (page, class) yes/no decisions that were correct |
| MAE count | average error in the number of instances per page |

**Detection** (only with `bbox`):

| metric | meaning |
|--------|---------|
| AP50 | average precision, counting a box as correct at IoU ≥ 0.5 |
| AP50-95 | AP averaged over IoU 0.5 to 0.95, which is stricter |
| mAP | AP averaged over classes |
| confusion matrix | rows are truth and columns are predictions. `background` counts false positives (row) and missed boxes (column) |

IoU is the overlap between a predicted and a true box (intersection divided by union). A box only matches if its class is also right.

## Useful options

| option | what it does |
|--------|--------------|
| `--split val` | `train`, `val`, `test`, a comma list like `val,test`, or `all` |
| `--threshold 0.5` | ignore predictions with a score below 0.5. Run it at several values to find a good cutoff |
| `--output results/run1` | save `results.json` (everything) and `per_image.csv` (one row per image, with missed and spurious classes) |
| `--json` | print machine-readable results instead of the report |
| `--strict` | fail if any image is missing from your predictions |
| `--oracle` | predict the ground truth. This must score 100% and checks the setup |

## Things to watch out for

- **Missing images:** images absent from your predictions count as "predicted nothing", and the report warns you. Predict every image in the split, or use `--strict` to catch gaps.
- **Filenames:** keys must match the image filename exactly, including the extension, spaces and a leading space (for example `" Eigemyrveien 7B_page_5.jpg"`). Use `--template` to get them right.
- **Which split to use:** `train` is for fitting your model. Report results on `test`, and use `val` for tuning thresholds.
- **Unknown labels:** unknown class names are ignored with a warning.
- **Images:** they are in `all_data_json/images/`, and `predict()` receives the full path.
- **Comparing runs:** keep each run's `--output` folder and compare the `results.json` files.
