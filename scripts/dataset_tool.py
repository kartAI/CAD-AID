#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "opencv-python-headless>=4.9",
#     "numpy>=1.26",
#     "pyyaml>=6.0",
# ]
# ///
"""
dataset_tool.py -- utilities for the CAD-AID YOLO datasets (data/, data_seg/).

Works against any dataset laid out like this (both data/ and data_seg/ are):

    <dataset>/
      data.yaml            # or *.yaml -- must define nc + names
      train/images/ train/labels/
      test/images/  test/labels/
      val/images/   val/labels/

Labels are plain YOLO .txt: "<class> <cx> <cy> <w> <h>" for detection boxes,
or "<class> <x1> <y1> <x2> <y2> ... <xn> <yn>" for segmentation polygons --
this tool auto-detects which one it's looking at per line, and treats a line
it can't parse (e.g. a non-numeric class token) as a skipped malformed line
rather than crashing, surfacing a count of those in `stats`.

Commands
--------

  extract     Copy the images + labels that contain the given class(es) into
              a new YOLO-format dataset under --output (with its own
              data.yaml). Non-matching instances are dropped from each label
              file; images left with zero instances are skipped by default.

  visualize   Draw the label boxes/polygons on top of the images and write
              the annotated copies into --output. Useful for eyeballing
              label quality for one or more classes.

  stats       Print per-class / per-split instance and file counts. Reads
              only -- writes nothing unless --json is given.

Examples
--------

  uv run scripts/dataset_tool.py stats --dataset data

  uv run scripts/dataset_tool.py extract --dataset data \\
      --classes fasade,snitt --output out/fasade_snitt_subset

  uv run scripts/dataset_tool.py visualize --dataset data_seg \\
      --output out/room_viz --split val --limit 25
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
import yaml

SPLITS = ("train", "test", "val")
IMAGE_EXTS = (".jpg", ".jpeg", ".png")

# BGR swatches (cv2 convention), cycled by class id.
PALETTE = [
    (60, 60, 220),    # red
    (80, 175, 76),    # green
    (219, 152, 52),   # blue
    (0, 140, 255),    # orange
    (182, 89, 155),   # purple
    (185, 178, 0),    # teal
    (0, 215, 255),    # yellow
    (147, 20, 255),   # pink
]


def color_for_class(cls_id: int) -> tuple[int, int, int]:
    return PALETTE[cls_id % len(PALETTE)]


# --------------------------------------------------------------------------
# dataset / label model
# --------------------------------------------------------------------------


@dataclass
class DatasetInfo:
    root: Path
    yaml_path: Path
    names: list[str]
    name_to_id: dict[str, int]


def load_dataset_info(dataset_root: Path) -> DatasetInfo:
    if not dataset_root.is_dir():
        sys.exit(f"error: dataset path does not exist: {dataset_root}")
    yaml_candidates = sorted(dataset_root.glob("*.yaml")) + sorted(dataset_root.glob("*.yml"))
    if not yaml_candidates:
        sys.exit(f"error: no data.yaml (or *.yaml) found in {dataset_root}")
    yaml_path = yaml_candidates[0]
    with open(yaml_path) as f:
        cfg = yaml.safe_load(f)
    names = cfg["names"]
    if isinstance(names, dict):
        names = [names[i] for i in sorted(names)]
    return DatasetInfo(
        root=dataset_root,
        yaml_path=yaml_path,
        names=list(names),
        name_to_id={n: i for i, n in enumerate(names)},
    )


def resolve_classes(info: DatasetInfo, requested: list[str] | None) -> list[int]:
    """Returns sorted class ids. Empty/None `requested` means 'all classes'."""
    if not requested:
        return list(range(len(info.names)))
    lower_map = {n.lower(): i for n, i in info.name_to_id.items()}
    ids: set[int] = set()
    for raw in requested:
        token = raw.strip()
        if not token:
            continue
        if token.isdigit():
            idx = int(token)
            if not (0 <= idx < len(info.names)):
                sys.exit(f"error: class id {idx} out of range (0..{len(info.names) - 1})")
            ids.add(idx)
        elif token.lower() in lower_map:
            ids.add(lower_map[token.lower()])
        else:
            available = ", ".join(info.names)
            sys.exit(f"error: unknown class {raw!r}; available classes: {available}")
    return sorted(ids)


@dataclass
class Instance:
    cls: int
    kind: str  # "bbox" | "polygon"
    coords: list[float]  # normalized 0..1


def parse_label_line(line: str) -> Instance | None:
    parts = line.strip().split()
    if not parts:
        return None
    try:
        cls = int(parts[0])
        coords = [float(p) for p in parts[1:]]
    except ValueError:
        return None  # malformed line (e.g. a non-numeric class token) -- skip, don't crash
    if len(coords) == 4:
        return Instance(cls=cls, kind="bbox", coords=coords)
    if len(coords) >= 6 and len(coords) % 2 == 0:
        return Instance(cls=cls, kind="polygon", coords=coords)
    return None


@dataclass
class ParsedLabel:
    instances: list[Instance] = field(default_factory=list)
    malformed_lines: int = 0


def read_label_file(path: Path) -> ParsedLabel:
    result = ParsedLabel()
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            if not raw_line.strip():
                continue
            inst = parse_label_line(raw_line)
            if inst is None:
                result.malformed_lines += 1
            else:
                result.instances.append(inst)
    return result


def iter_split_pairs(dataset_root: Path, split: str):
    """Yields (image_path, label_path_or_None) for every image in a split."""
    img_dir = dataset_root / split / "images"
    lbl_dir = dataset_root / split / "labels"
    if not img_dir.is_dir():
        return
    for img_path in sorted(img_dir.iterdir()):
        if img_path.suffix.lower() not in IMAGE_EXTS:
            continue
        lbl_path = lbl_dir / (img_path.stem + ".txt")
        yield img_path, (lbl_path if lbl_path.is_file() else None)


def selected_splits(args: argparse.Namespace) -> list[str]:
    if not args.split:
        return list(SPLITS)
    chosen = [s.strip() for s in args.split.split(",") if s.strip()]
    for s in chosen:
        if s not in SPLITS:
            sys.exit(f"error: unknown split {s!r}; choose from {', '.join(SPLITS)}")
    return chosen


# --------------------------------------------------------------------------
# stats
# --------------------------------------------------------------------------


def cmd_stats(args: argparse.Namespace) -> None:
    info = load_dataset_info(Path(args.dataset))
    class_ids = resolve_classes(info, args.classes)
    splits = selected_splits(args)

    per_split: dict[str, dict] = {}
    class_totals = {c: 0 for c in class_ids}
    grand_images = grand_labeled = grand_empty = grand_missing = grand_instances = grand_malformed = 0

    for split in splits:
        n_images = n_labeled = n_empty = n_missing = n_instances = n_malformed = 0
        class_counts = {c: 0 for c in class_ids}
        images_with_selected = 0

        for img_path, lbl_path in iter_split_pairs(info.root, split):
            n_images += 1
            if lbl_path is None:
                n_missing += 1
                continue
            n_labeled += 1
            parsed = read_label_file(lbl_path)
            n_malformed += parsed.malformed_lines
            if not parsed.instances:
                n_empty += 1
                continue
            n_instances += len(parsed.instances)
            has_selected = False
            for inst in parsed.instances:
                if inst.cls in class_counts:
                    class_counts[inst.cls] += 1
                    has_selected = True
            if has_selected:
                images_with_selected += 1

        per_split[split] = dict(
            images=n_images,
            labeled=n_labeled,
            missing_label=n_missing,
            empty_label=n_empty,
            instances=n_instances,
            malformed=n_malformed,
            images_with_selected=images_with_selected,
            class_counts=class_counts,
        )
        for c in class_ids:
            class_totals[c] += class_counts[c]
        grand_images += n_images
        grand_labeled += n_labeled
        grand_empty += n_empty
        grand_missing += n_missing
        grand_instances += n_instances
        grand_malformed += n_malformed

    grand_selected_instances = sum(class_totals.values())

    # ---- render ----
    print(f"\nDataset: {info.root}  ({info.yaml_path.name})")
    print(f"Classes: {', '.join(f'{i}={n}' for i, n in enumerate(info.names))}")
    if args.classes:
        print(f"Filtered to: {', '.join(info.names[c] for c in class_ids)}")

    print("\nPer-split file stats:")
    _print_table(
        headers=["split", "images", "label files", "instances", "empty labels", "no label file", "malformed lines"],
        rows=[
            [s, d["images"], d["labeled"], d["instances"], d["empty_label"], d["missing_label"], d["malformed"]]
            for s, d in per_split.items()
        ]
        + [["TOTAL", grand_images, grand_labeled, grand_instances, grand_empty, grand_missing, grand_malformed]],
    )

    print("\nPer-class instance counts:")
    class_rows = []
    for c in sorted(class_ids, key=lambda c: -class_totals[c]):
        row = [info.names[c]] + [per_split[s]["class_counts"][c] for s in splits]
        total = class_totals[c]
        pct = f"{100 * total / grand_selected_instances:.1f}%" if grand_selected_instances else "0.0%"
        row += [total, pct]
        class_rows.append(row)
    class_rows.append(
        ["TOTAL"]
        + [sum(per_split[s]["class_counts"][c] for c in class_ids) for s in splits]
        + [grand_selected_instances, "100.0%"]
    )
    _print_table(headers=["class"] + list(splits) + ["total", "share"], rows=class_rows)
    print()

    if args.json:
        payload = {
            "dataset": str(info.root),
            "classes": info.names,
            "filtered_to": [info.names[c] for c in class_ids],
            "per_split": per_split,
            "class_totals": {info.names[c]: n for c, n in class_totals.items()},
            "totals": {
                "images": grand_images,
                "label_files": grand_labeled,
                "instances": grand_instances,
                "empty_label_files": grand_empty,
                "images_without_label_file": grand_missing,
                "malformed_lines": grand_malformed,
            },
        }
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2))
        print(f"Wrote {out_path}")


def _print_table(headers: list[str], rows: list[list]) -> None:
    str_rows = [[str(c) for c in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in str_rows)) if str_rows else len(h) for i, h in enumerate(headers)]
    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in str_rows:
        print(fmt.format(*row))


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def cmd_extract(args: argparse.Namespace) -> None:
    info = load_dataset_info(Path(args.dataset))
    class_ids = resolve_classes(info, args.classes)
    splits = selected_splits(args)
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    remap = {c: i for i, c in enumerate(class_ids)} if args.remap_ids else {c: c for c in class_ids}
    out_names = [info.names[c] for c in class_ids] if args.remap_ids else info.names

    total_images = total_instances = 0
    per_class_images = {c: 0 for c in class_ids}
    per_class_instances = {c: 0 for c in class_ids}

    for split in splits:
        out_img_dir = out_root / split / "images"
        out_lbl_dir = out_root / split / "labels"
        split_images = split_instances = 0

        for img_path, lbl_path in iter_split_pairs(info.root, split):
            if lbl_path is None:
                continue
            parsed = read_label_file(lbl_path)
            kept = [inst for inst in parsed.instances if inst.cls in remap]
            if not kept and not args.include_empty:
                continue

            out_img_dir.mkdir(parents=True, exist_ok=True)
            out_lbl_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img_path, out_img_dir / img_path.name)
            lines = []
            for inst in kept:
                new_cls = remap[inst.cls]
                lines.append(f"{new_cls} " + " ".join(f"{v:.6f}" for v in inst.coords))
                per_class_instances[inst.cls] += 1
                split_instances += 1
            (out_lbl_dir / (img_path.stem + ".txt")).write_text("\n".join(lines) + ("\n" if lines else ""))

            split_images += 1
            classes_in_image = {inst.cls for inst in kept}
            for c in classes_in_image:
                per_class_images[c] += 1

        total_images += split_images
        total_instances += split_instances
        print(f"{split}: {split_images} images, {split_instances} instances")

    out_yaml = {
        "path": ".",
        "train": "train/images",
        "test": "test/images",
        "val": "val/images",
        "nc": len(out_names),
        "names": out_names,
    }
    (out_root / "data.yaml").write_text(yaml.safe_dump(out_yaml, sort_keys=False))

    print(f"\nExtracted {total_images} images / {total_instances} instances -> {out_root}")
    print("Per-class:")
    _print_table(
        headers=["class", "images", "instances"],
        rows=[[info.names[c], per_class_images[c], per_class_instances[c]] for c in class_ids],
    )
    print(f"Wrote {out_root / 'data.yaml'}")


# --------------------------------------------------------------------------
# visualize
# --------------------------------------------------------------------------


def draw_instance(img: np.ndarray, inst: Instance, label: str, color: tuple[int, int, int]) -> None:
    h, w = img.shape[:2]
    if inst.kind == "bbox":
        cx, cy, bw, bh = inst.coords
        x1, y1 = int((cx - bw / 2) * w), int((cy - bh / 2) * h)
        x2, y2 = int((cx + bw / 2) * w), int((cy + bh / 2) * h)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        anchor = (x1, max(y1, 14))
    else:
        pts = inst.coords
        poly = np.array(
            [(int(pts[i] * w), int(pts[i + 1] * h)) for i in range(0, len(pts), 2)],
            dtype=np.int32,
        )
        overlay = img.copy()
        cv2.fillPoly(overlay, [poly], color)
        cv2.addWeighted(overlay, 0.25, img, 0.75, 0, dst=img)
        cv2.polylines(img, [poly], isClosed=True, color=color, thickness=2)
        anchor = (int(poly[:, 0].min()), max(int(poly[:, 1].min()), 14))

    (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    tx, ty = anchor
    cv2.rectangle(img, (tx, ty - th - baseline - 2), (tx + tw + 6, ty + 2), color, -1)
    cv2.putText(img, label, (tx + 3, ty - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def draw_legend(img: np.ndarray, entries: list[tuple[str, tuple[int, int, int]]]) -> None:
    if not entries:
        return
    pad, swatch, line_h = 8, 14, 20
    width = max(cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0][0] for name, _ in entries) + swatch + pad * 3
    height = line_h * len(entries) + pad
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (width, height), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.65, img, 0.35, 0, dst=img)
    for i, (name, color) in enumerate(entries):
        y = pad + i * line_h
        cv2.rectangle(img, (pad, y + 2), (pad + swatch, y + swatch + 2), color, -1)
        cv2.putText(img, name, (pad + swatch + 6, y + swatch), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def cmd_visualize(args: argparse.Namespace) -> None:
    info = load_dataset_info(Path(args.dataset))
    class_ids = resolve_classes(info, args.classes)
    class_id_set = set(class_ids)
    splits = selected_splits(args)
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    written = skipped_no_match = skipped_unreadable = 0

    for split in splits:
        pairs = [p for p in iter_split_pairs(info.root, split) if p[1] is not None]
        if args.limit:
            rng.shuffle(pairs)
            pairs = pairs[: args.limit]

        out_dir = out_root / split
        for img_path, lbl_path in pairs:
            parsed = read_label_file(lbl_path)
            relevant = [inst for inst in parsed.instances if inst.cls in class_id_set]
            if not relevant and not args.include_empty:
                skipped_no_match += 1
                continue

            img = cv2.imread(str(img_path))
            if img is None:
                skipped_unreadable += 1
                continue

            used_classes: dict[int, tuple[str, tuple[int, int, int]]] = {}
            for inst in relevant:
                name = info.names[inst.cls]
                color = color_for_class(inst.cls)
                draw_instance(img, inst, name, color)
                used_classes[inst.cls] = (name, color)

            if args.legend:
                draw_legend(img, sorted(used_classes.values()))

            out_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_dir / img_path.name), img)
            written += 1

    print(f"Wrote {written} annotated image(s) to {out_root}")
    if skipped_no_match:
        print(f"Skipped {skipped_no_match} image(s) with no instance of the selected class(es)")
    if skipped_unreadable:
        print(f"Skipped {skipped_unreadable} image(s) OpenCV could not read")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract, visualize, and report stats on the CAD-AID YOLO datasets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dataset", required=True, help="Path to a YOLO dataset root (e.g. data or data_seg)")
    common.add_argument("--split", help="Comma-separated subset of train,test,val (default: all)")

    classes_arg = dict(
        help="Comma-separated class names or ids (e.g. 'fasade,snitt' or '0,3'). Default: all classes.",
    )

    p_stats = sub.add_parser("stats", parents=[common], help="Print per-class / per-split dataset stats")
    p_stats.add_argument("--classes", **classes_arg)
    p_stats.add_argument("--json", help="Also write the stats as JSON to this path")
    p_stats.set_defaults(func=cmd_stats)

    p_extract = sub.add_parser("extract", parents=[common], help="Copy images+labels for given classes into a new dataset")
    p_extract.add_argument("--classes", required=True, **classes_arg)
    p_extract.add_argument("--output", required=True, help="Output folder for the extracted dataset")
    p_extract.add_argument(
        "--include-empty",
        action="store_true",
        help="Also copy images that end up with zero instances of the selected classes",
    )
    p_extract.add_argument(
        "--no-remap-ids",
        dest="remap_ids",
        action="store_false",
        help="Keep original class ids in the output labels/data.yaml instead of remapping to 0..N-1",
    )
    p_extract.set_defaults(func=cmd_extract, remap_ids=True)

    p_viz = sub.add_parser("visualize", parents=[common], help="Draw labels on top of images for visual inspection")
    p_viz.add_argument("--classes", **classes_arg)
    p_viz.add_argument("--output", required=True, help="Output folder for the annotated images")
    p_viz.add_argument("--limit", type=int, help="Max images per split (randomly sampled)")
    p_viz.add_argument("--seed", type=int, default=0, help="Random seed used with --limit (default: 0)")
    p_viz.add_argument(
        "--include-empty",
        action="store_true",
        help="Also write images that have no instance of the selected class(es) (drawn with no boxes)",
    )
    p_viz.add_argument("--no-legend", dest="legend", action="store_false", help="Don't draw the class-color legend")
    p_viz.set_defaults(func=cmd_visualize, legend=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "classes", None):
        args.classes = [c for c in args.classes.split(",") if c.strip()]
    args.func(args)


if __name__ == "__main__":
    main()
