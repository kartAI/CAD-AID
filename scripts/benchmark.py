#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
benchmark.py -- score any drawing-type classifier/detector on all_data_json/.

You don't need to know the dataset layout. Give it predictions (a file or a
Python function) and get a full report.

What is measured
----------------
  Classification  (always)  Image-level, multi-label: "which drawing types are
                            on this page?"  Per-class precision/recall/F1/
                            support, micro/macro/weighted F1, exact-match,
                            Hamming accuracy, per-class count error.
  Detection       (only if predictions carry `bbox`)  Per-class AP@0.5 and
                            AP@[.5:.95], mAP, precision/recall at IoU 0.5,
                            class-agnostic confusion matrix (incl. background).

Classes: 0 fasade, 1 plantegning, 2 situasjonskart, 3 snitt (read from the data).

Prediction format
-----------------
Simplest form: just class names (or ids) per image, e.g. ["fasade", "snitt"],
[] for none. Repeating a name counts as multiple instances. Otherwise a
prediction is {"label": <id or name>, "score": 0..1 (optional, default 1),
"bbox": [x1, y1, x2, y2] in pixels (optional)}. `"text"` is accepted as an
alias for `"label"`.

  Option A -- JSON file (--predictions preds.json):
      {"<image filename>": [<prediction>, ...], ...}   e.g. {"a.jpg": ["fasade"]}
      or [{"image": "<filename>", "predictions": [<prediction>, ...]}, ...]
      Run with --template to write a ready-to-fill file for your split.

  Option B -- Python function (--predictor my_model.py:predict):
      def predict(image_path: str) -> list:   # <prediction>s, or just class names
      Called once per image; the benchmark handles the rest.

Examples
--------
  uv run scripts/benchmark.py --template preds.json --split test
  uv run scripts/benchmark.py --predictions preds.json --split test
  uv run scripts/benchmark.py --predictor my_model.py:predict --split val \\
      --threshold 0.5 --output results/run1
  uv run scripts/benchmark.py --oracle          # sanity check: must score 100%
  uv run scripts/benchmark.py --predictions preds.json --json   # machine-readable

Outputs (with --output DIR): results.json (everything), per_image.csv.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "all_data_json"
IOU_THRS = [round(0.5 + 0.05 * i, 2) for i in range(10)]
SPLITS = ("train", "val", "test")


# ----------------------------------------------------------------- loading
def load_dataset(data_dir: Path, splits: list[str]):
    records = json.loads((data_dir / "labels.json").read_text())
    names: dict[int, str] = {}
    for r in records:
        for l in r["labels"]:
            names[l["label"]] = l["text"]
    records = [r for r in records if r["split"] in splits]
    if not records:
        sys.exit(f"No images found for split(s): {', '.join(splits)}")
    return records, dict(sorted(names.items()))


def parse_predictions(raw, names: dict[int, str]):
    """Normalise any accepted predictions layout -> {image: [pred, ...]}."""
    by_name = {v: k for k, v in names.items()}
    if isinstance(raw, list):
        raw = {e["image"]: e.get("predictions", []) for e in raw}
    out, bad = {}, 0
    for img, preds in raw.items():
        clean = []
        if preds is None:
            preds = []
        elif isinstance(preds, (str, int)):
            preds = [preds]
        for p in preds:
            if not isinstance(p, dict):  # bare class name or id
                p = {"label": p}
            lab = p.get("label", p.get("text", p.get("class")))
            if isinstance(lab, str) and not lab.isdigit():
                lab = by_name.get(lab.strip().lower())
            elif lab is not None:
                lab = int(lab)
            if lab not in names:
                bad += 1
                continue
            bbox = p.get("bbox")
            clean.append({"label": lab, "score": float(p.get("score", 1.0)),
                          "bbox": [float(v) for v in bbox] if bbox else None})
        out[img] = clean
    if bad:
        print(f"warning: ignored {bad} prediction(s) with unknown labels", file=sys.stderr)
    return out


def run_predictor(spec: str, records, data_dir: Path):
    path, _, fn = spec.partition(":")
    if not fn:
        sys.exit("--predictor must look like path/to/file.py:function_name")
    mod_spec = importlib.util.spec_from_file_location("user_predictor", path)
    mod = importlib.util.module_from_spec(mod_spec)
    sys.path.insert(0, str(Path(path).resolve().parent))
    mod_spec.loader.exec_module(mod)
    predict = getattr(mod, fn)
    raw, t0 = {}, time.perf_counter()
    for i, r in enumerate(records, 1):
        raw[r["image"]] = predict(str(data_dir / "images" / r["image"]))
        if i % 25 == 0 or i == len(records):
            print(f"  predicted {i}/{len(records)}", file=sys.stderr, end="\r")
    print(file=sys.stderr)
    return raw, time.perf_counter() - t0


# ----------------------------------------------------------------- metrics
def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def iou(a, b):
    iw = min(a[2], b[2]) - max(a[0], b[0])
    ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    inter = iw * ih
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def classification_metrics(records, preds, names, threshold):
    ids = list(names)
    c = {k: {"tp": 0, "fp": 0, "fn": 0, "support": 0, "count_abs_err": 0, "gt_instances": 0}
         for k in ids}
    exact = hamming = 0
    rows = []
    for r in records:
        gt = defaultdict(int)
        for l in r["labels"]:
            gt[l["label"]] += 1
        pr = defaultdict(int)
        for p in preds.get(r["image"], []):
            if p["score"] >= threshold:
                pr[p["label"]] += 1
        g, p_ = {k for k in ids if gt[k]}, {k for k in ids if pr[k]}
        for k in ids:
            c[k]["tp"] += k in g and k in p_
            c[k]["fp"] += k not in g and k in p_
            c[k]["fn"] += k in g and k not in p_
            c[k]["support"] += k in g
            c[k]["gt_instances"] += gt[k]
            c[k]["count_abs_err"] += abs(gt[k] - pr[k])
        exact += g == p_
        hamming += sum((k in g) == (k in p_) for k in ids) / len(ids)
        rows.append({"image": r["image"], "split": r["split"],
                     "gt": sorted(names[k] for k in g), "pred": sorted(names[k] for k in p_),
                     "correct": g == p_,
                     "missed": sorted(names[k] for k in g - p_),
                     "spurious": sorted(names[k] for k in p_ - g),
                     "gt_count": sum(gt.values()), "pred_count": sum(pr.values())})
    per_class = {}
    for k in ids:
        p, r_, f = prf(c[k]["tp"], c[k]["fp"], c[k]["fn"])
        n = len(records)
        per_class[names[k]] = {**c[k], "precision": p, "recall": r_, "f1": f,
                               "mean_abs_count_error": c[k]["count_abs_err"] / n}
    tp, fp, fn = (sum(c[k][x] for k in ids) for x in ("tp", "fp", "fn"))
    mp, mr, mf = prf(tp, fp, fn)
    sup = sum(c[k]["support"] for k in ids) or 1
    n = len(records)
    summary = {
        "images": n, "micro_precision": mp, "micro_recall": mr, "micro_f1": mf,
        "macro_f1": sum(v["f1"] for v in per_class.values()) / len(ids),
        "weighted_f1": sum(per_class[names[k]]["f1"] * c[k]["support"] for k in ids) / sup,
        "exact_match": exact / n, "hamming_accuracy": hamming / n,
    }
    return summary, per_class, rows


def average_precision(scores_tp, n_gt):
    """All-point interpolated AP from [(score, is_tp)] sorted desc."""
    if n_gt == 0:
        return None
    scores_tp.sort(key=lambda x: -x[0])
    tp = fp = 0
    rec, prec = [], []
    for _, hit in scores_tp:
        tp += hit
        fp += not hit
        rec.append(tp / n_gt)
        prec.append(tp / (tp + fp))
    mrec, mpre = [0.0] + rec + [1.0], [0.0] + prec + [0.0]
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    return sum((mrec[i] - mrec[i - 1]) * mpre[i] for i in range(1, len(mrec)) if mrec[i] != mrec[i - 1])


def match_image(gts, dets, thr):
    """Greedy match (dets sorted by score). Returns list of (det_idx, gt_idx|None)."""
    used, out = set(), []
    for di, d in sorted(enumerate(dets), key=lambda x: -x[1]["score"]):
        best, bj = thr, None
        for gj, g in enumerate(gts):
            if gj in used or g["label"] != d["label"]:
                continue
            v = iou(d["bbox"], g["bbox"])
            if v >= best:
                best, bj = v, gj
        if bj is not None:
            used.add(bj)
        out.append((di, bj))
    return out


def detection_metrics(records, preds, names, threshold):
    ids = list(names)
    ap = {k: {t: [] for t in IOU_THRS} for k in ids}
    n_gt = {k: 0 for k in ids}
    for r in records:
        gts = [{"label": l["label"], "bbox": l["bbox"]} for l in r["labels"]]
        dets = [p for p in preds.get(r["image"], []) if p["bbox"] and p["score"] >= threshold]
        for k in ids:
            n_gt[k] += sum(g["label"] == k for g in gts)
            kg = [g for g in gts if g["label"] == k]
            kd = [d for d in dets if d["label"] == k]
            for t in IOU_THRS:
                for di, gj in match_image(kg, kd, t):
                    ap[k][t].append((kd[di]["score"], gj is not None))
    per_class, maps50, maps = {}, [], []
    for k in ids:
        a50 = average_precision(list(ap[k][0.5]), n_gt[k])
        aps = [average_precision(list(ap[k][t]), n_gt[k]) for t in IOU_THRS]
        a = None if n_gt[k] == 0 else sum(aps) / len(aps)
        tp = sum(h for _, h in ap[k][0.5])
        fp = len(ap[k][0.5]) - tp
        p, rc, f = prf(tp, fp, n_gt[k] - tp)
        per_class[names[k]] = {"ap50": a50, "ap50_95": a, "precision@0.5": p, "recall@0.5": rc,
                               "f1@0.5": f, "gt_boxes": n_gt[k], "pred_boxes": len(ap[k][0.5])}
        if a50 is not None:
            maps50.append(a50)
            maps.append(a)
    # class-agnostic confusion at IoU 0.5 (rows = truth, cols = prediction)
    labels = [names[k] for k in ids] + ["background"]
    idx = {k: i for i, k in enumerate(ids)}
    bg = len(ids)
    cm = [[0] * len(labels) for _ in labels]
    for r in records:
        dets = sorted([p for p in preds.get(r["image"], []) if p["bbox"] and p["score"] >= threshold],
                      key=lambda d: -d["score"])
        gts = r["labels"]
        used = set()
        for d in dets:
            best, bj = 0.5, None
            for gj, g in enumerate(gts):
                if gj in used:
                    continue
                v = iou(d["bbox"], g["bbox"])
                if v >= best:
                    best, bj = v, gj
            if bj is None:
                cm[bg][idx[d["label"]]] += 1
            else:
                used.add(bj)
                cm[idx[gts[bj]["label"]]][idx[d["label"]]] += 1
        for gj, g in enumerate(gts):
            if gj not in used:
                cm[idx[g["label"]]][bg] += 1
    summary = {"mAP50": sum(maps50) / len(maps50) if maps50 else None,
               "mAP50_95": sum(maps) / len(maps) if maps else None}
    return summary, per_class, {"labels": labels, "matrix": cm}


# ----------------------------------------------------------------- output
def pct(v):
    return "  n/a " if v is None else f"{v * 100:5.1f}%"


def table(header, rows):
    w = [max(len(str(x)) for x in col) for col in zip(header, *rows)]
    fmt = lambda r: "  ".join(str(x).ljust(w[0]) if i == 0 else str(x).rjust(w[i]) for i, x in enumerate(r))
    return "\n".join([fmt(header), "  ".join("-" * x for x in w), *map(fmt, rows)])


def print_report(res):
    m = res["meta"]
    print(f"\n=== CAD-AID benchmark | split: {','.join(m['splits'])} | {m['images']} images "
          f"| threshold {m['threshold']} ===")
    if m.get("inference_seconds") is not None:
        print(f"inference: {m['inference_seconds']:.1f}s ({m['inference_seconds'] / m['images'] * 1000:.0f} ms/image)")
    if m["missing_predictions"]:
        print(f"warning: {m['missing_predictions']} image(s) had no entry in the predictions (counted as empty)")
    s = res["classification"]["summary"]
    print("\n-- Classification (image level, multi-label) --")
    print(f"micro F1 {pct(s['micro_f1'])} | macro F1 {pct(s['macro_f1'])} | weighted F1 {pct(s['weighted_f1'])} "
          f"| exact match {pct(s['exact_match'])} | hamming acc {pct(s['hamming_accuracy'])}")
    print(table(["class", "prec", "recall", "F1", "support", "TP", "FP", "FN", "MAE count"],
                [[k, pct(v["precision"]), pct(v["recall"]), pct(v["f1"]), v["support"], v["tp"], v["fp"],
                  v["fn"], f"{v['mean_abs_count_error']:.3f}"]
                 for k, v in res["classification"]["per_class"].items()]))
    if "detection" in res:
        d = res["detection"]
        print("\n-- Detection (bbox) --")
        print(f"mAP@0.5 {pct(d['summary']['mAP50'])} | mAP@[.5:.95] {pct(d['summary']['mAP50_95'])}")
        print(table(["class", "AP50", "AP50-95", "prec@.5", "rec@.5", "GT boxes", "pred boxes"],
                    [[k, pct(v["ap50"]), pct(v["ap50_95"]), pct(v["precision@0.5"]), pct(v["recall@0.5"]),
                      v["gt_boxes"], v["pred_boxes"]] for k, v in d["per_class"].items()]))
        cm = d["confusion"]
        print("\nConfusion @IoU 0.5 (rows = truth, cols = predicted):")
        print(table(["truth \\ pred", *cm["labels"]], [[l, *row] for l, row in zip(cm["labels"], cm["matrix"])]))
    else:
        print("\n(no bbox in predictions -> detection metrics skipped)")
    bad = [r for r in res["per_image"] if not r["correct"]]
    print(f"\nMisclassified images: {len(bad)}/{len(res['per_image'])} (first 10; all in per_image.csv with --output):")
    for r in bad[:10]:
        print(f"  {r['image']}: missed={r['missed'] or '-'} spurious={r['spurious'] or '-'}")
    print()


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--predictions", type=Path, help="predictions JSON file")
    src.add_argument("--predictor", help="python file and function, e.g. my_model.py:predict")
    src.add_argument("--oracle", action="store_true", help="predict ground truth (sanity check, 100%%)")
    src.add_argument("--template", type=Path, help="write a fill-in predictions file and exit")
    ap.add_argument("--split", default="test", help="train, val, test, comma list, or 'all' (default: test)")
    ap.add_argument("--threshold", type=float, default=0.0, help="drop predictions below this score")
    ap.add_argument("--data", type=Path, default=DATA_DIR, help="dataset dir (default: all_data_json)")
    ap.add_argument("--output", type=Path, help="directory for results.json and per_image.csv")
    ap.add_argument("--json", action="store_true", help="print results JSON to stdout instead of the report")
    ap.add_argument("--strict", action="store_true", help="fail if any image is missing from predictions")
    a = ap.parse_args()

    splits = list(SPLITS) if a.split == "all" else a.split.split(",")
    records, names = load_dataset(a.data, splits)

    if a.template:
        a.template.write_text(json.dumps({r["image"]: [] for r in records}, ensure_ascii=False, indent=1))
        print(f"Wrote {a.template} ({len(records)} images). Fill each list with "
              f'{{"label": "fasade", "score": 0.9, "bbox": [x1,y1,x2,y2]}} entries (bbox optional).\n'
              f"Classes: {names}")
        return

    secs = None
    if a.oracle:
        raw = {r["image"]: [{"label": l["label"], "bbox": l["bbox"]} for l in r["labels"]] for r in records}
    elif a.predictor:
        raw, secs = run_predictor(a.predictor, records, a.data)
    elif a.predictions:
        raw = json.loads(a.predictions.read_text())
    else:
        ap.error("provide one of --predictions, --predictor, --oracle, --template")

    preds = parse_predictions(raw, names)
    missing = [r["image"] for r in records if r["image"] not in preds]
    if missing and a.strict:
        sys.exit(f"{len(missing)} images missing from predictions, e.g. {missing[:3]}")

    csum, cclass, rows = classification_metrics(records, preds, names, a.threshold)
    res = {"meta": {"splits": splits, "images": len(records), "threshold": a.threshold,
                    "missing_predictions": len(missing), "inference_seconds": secs,
                    "classes": names},
           "classification": {"summary": csum, "per_class": cclass},
           "per_image": rows}
    if any(p["bbox"] for ps in preds.values() for p in ps):
        dsum, dclass, cm = detection_metrics(records, preds, names, a.threshold)
        res["detection"] = {"summary": dsum, "per_class": dclass, "confusion": cm}

    if a.output:
        a.output.mkdir(parents=True, exist_ok=True)
        (a.output / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
        with open(a.output / "per_image.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["image", "split", "correct", "gt", "pred", "missed", "spurious", "gt_count", "pred_count"])
            for r in rows:
                w.writerow([r["image"], r["split"], r["correct"], "|".join(r["gt"]), "|".join(r["pred"]),
                            "|".join(r["missed"]), "|".join(r["spurious"]), r["gt_count"], r["pred_count"]])
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print_report(res)
        if a.output:
            print(f"Saved results to {a.output}/")


if __name__ == "__main__":
    main()
