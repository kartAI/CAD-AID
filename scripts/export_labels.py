#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow>=10.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
export_labels.py -- flatten a YOLO dataset (data/) into one labels.json + one images folder.

Output layout:

    <output>/
      labels.json    # [{"image", "split", "width", "height",
                     #   "labels": [{"label", "text", "bbox": [x1, y1, x2, y2]}]}]
      images/        # every image, regardless of split
      pdf/           # one PDF per image (only with --pdf)
      viewer.html    # copy of scripts/viewer.html (open it directly)

bbox is in pixels (x1, y1, x2, y2). Segmentation polygons are reduced to their
bounding box. Images whose file name collides across splits get a "<split>_" prefix.

Examples:
  uv run scripts/export_labels.py
  uv run scripts/export_labels.py --splits train,val --classes fasade,snitt --pdf
  uv run scripts/export_labels.py --limit 20 --output out/sample
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml
from PIL import Image, ImageOps

IMG_EXTS = {".jpg", ".jpeg", ".png"}
HERE = Path(__file__).resolve().parent


def parse_label_file(path: Path) -> list[tuple[int, list[float]]]:
    """Return [(class_id, [cx, cy, w, h] normalized)]; skips malformed lines."""
    out = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        parts = line.split()
        try:
            cls = int(parts[0])
            nums = [float(p) for p in parts[1:]]
        except (ValueError, IndexError):
            continue
        if len(nums) == 4:
            out.append((cls, nums))
        elif len(nums) >= 6 and len(nums) % 2 == 0:  # polygon -> bbox
            xs, ys = nums[0::2], nums[1::2]
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            out.append((cls, [(x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1]))
    return out


def resolve_classes(arg: str | None, names: list[str]) -> set[int] | None:
    if not arg:
        return None
    ids = set()
    for tok in (t.strip() for t in arg.split(",") if t.strip()):
        if tok.isdigit():
            ids.add(int(tok))
        elif tok in names:
            ids.add(names.index(tok))
        else:
            sys.exit(f"Unknown class '{tok}'. Available: {names}")
    return ids


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", type=Path, default=Path("data"))
    ap.add_argument("--output", type=Path, default=Path("export"))
    ap.add_argument("--splits", default="train,val,test", help="comma-separated (default: all)")
    ap.add_argument("--classes", help="only keep these classes (names or ids, comma-separated)")
    ap.add_argument("--limit", type=int, help="max number of images to export")
    ap.add_argument("--skip-empty", action="store_true", help="drop images with no (matching) labels; default keeps them as null results")
    ap.add_argument("--pdf", action="store_true", help="also write one PDF per image to <output>/pdf/")
    args = ap.parse_args()

    cfg = yaml.safe_load((args.dataset / "data.yaml").read_text())
    names = list(cfg["names"].values()) if isinstance(cfg["names"], dict) else list(cfg["names"])
    keep = resolve_classes(args.classes, names)

    img_dir = args.output / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        (args.output / "pdf").mkdir(exist_ok=True)

    records, used = [], set()
    per_split = Counter()
    per_class_inst, per_class_imgs = Counter(), Counter()
    skipped_empty = 0
    total = sum(
        1
        for s in (s.strip() for s in args.splits.split(",") if s.strip())
        if (args.dataset / s / "images").is_dir()
        for f in (args.dataset / s / "images").iterdir()
        if f.suffix.lower() in IMG_EXTS
    )
    if args.limit:
        total = min(total, args.limit)
    seen = 0
    print(f"Found {total} candidate images in {args.dataset}/", flush=True)

    for split in (s.strip() for s in args.splits.split(",") if s.strip()):
        src_dir = args.dataset / split / "images"
        if not src_dir.is_dir():
            print(f"warning: missing {src_dir}", file=sys.stderr)
            continue
        for img in sorted(src_dir.iterdir()):
            if args.limit and len(records) >= args.limit:
                break
            if img.suffix.lower() not in IMG_EXTS:
                continue
            seen += 1
            if seen % 25 == 0 or seen == total:
                print(f"  [{split}] {seen}/{total} scanned, {len(records)} exported", flush=True)
            labs = parse_label_file(args.dataset / split / "labels" / f"{img.stem}.txt")
            if keep is not None:
                labs = [l for l in labs if l[0] in keep]
            if not labs and args.skip_empty:
                skipped_empty += 1
                continue

            name = img.name
            if name.lower() in used:
                name = f"{split}_{name}"
            used.add(name.lower())

            with Image.open(img) as im:
                im = ImageOps.exif_transpose(im)
                w, h = im.size
                if args.pdf:
                    im.convert("RGB").save(args.output / "pdf" / f"{Path(name).stem}.pdf", resolution=150.0)
            shutil.copy2(img, img_dir / name)

            labels = []
            for cls, (cx, cy, bw, bh) in labs:
                labels.append({
                    "label": cls,
                    "text": names[cls] if cls < len(names) else str(cls),
                    "bbox": [round((cx - bw / 2) * w, 1), round((cy - bh / 2) * h, 1),
                             round((cx + bw / 2) * w, 1), round((cy + bh / 2) * h, 1)],
                })
            records.append({"image": name, "split": split, "width": w, "height": h, "labels": labels})
            per_split[split] += 1
            for l in labels:
                per_class_inst[l["text"]] += 1
            for t in {l["text"] for l in labels}:
                per_class_imgs[t] += 1

    (args.output / "labels.json").write_text(json.dumps(records, ensure_ascii=False, indent=1))
    viewer = HERE / "viewer.html"
    if viewer.exists():
        shutil.copy2(viewer, args.output / "viewer.html")

    n_inst = sum(per_class_inst.values())
    print(f"\nExported {len(records)} images, {n_inst} labels -> {args.output}/")
    if args.pdf:
        print(f"PDFs: {len(records)} -> {args.output}/pdf/")
    n_empty = sum(1 for r in records if not r["labels"])
    print(f"Images with no labels (null results): {n_empty}")
    if skipped_empty:
        print(f"Skipped {skipped_empty} images with no (matching) labels")
    print("\nPer split (images):")
    for s, c in per_split.items():
        print(f"  {s:<8}{c:>6}")
    print(f"\n{'Class':<16}{'instances':>10}{'images':>9}{'avg/img':>9}")
    for t in sorted(per_class_inst, key=per_class_inst.get, reverse=True):
        print(f"{t:<16}{per_class_inst[t]:>10}{per_class_imgs[t]:>9}{per_class_inst[t] / per_class_imgs[t]:>9.2f}")
    if records:
        print(f"\nAvg labels/image: {n_inst / len(records):.2f}")


if __name__ == "__main__":
    main()
