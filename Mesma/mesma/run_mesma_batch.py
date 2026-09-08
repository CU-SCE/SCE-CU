#!/usr/bin/env python3
"""
Batch MESMA runner with progress bars.

Example (single image):
  PYTHONUNBUFFERED=1 conda run --no-capture-output -n mesma python run_mesma_batch.py \
    --library internal_scripts/spectral_library/38_output.sli \
    --class-name Type \
    --image /tmp/mesma_test/10_S_EG_2024_10_30.tif

Example (folder):
  ... --image-dir /tmp/mesma_test
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np


def setup_qgis_paths() -> None:
    candidates = [
        Path("/opt/conda/envs/mesma"),
        Path("/opt/conda/envs/earth-lab"),
        Path("/opt/conda/envs/macrosystems"),
        Path(os.environ["CONDA_PREFIX"]) if os.environ.get("CONDA_PREFIX") else None,
    ]
    qgis_python = None
    for env in candidates:
        if env is None:
            continue
        share = env / "share" / "qgis" / "python"
        if share.exists():
            qgis_python = share
            print(f"Using QGIS from: {env}", flush=True)
            break
    if qgis_python is None:
        raise RuntimeError("QGIS not found. Use conda env 'mesma'.")
    sys.path.append(str(qgis_python / "plugins"))
    sys.path.append(str(qgis_python))


def bar(fraction: float, width: int = 20) -> str:
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(width * fraction))
    return f"{'█' * filled}{'-' * (width - filled)}"


def show_progress(index: int, total: int, name: str) -> None:
    frac = index / total if total else 1.0
    pct = int(round(100 * frac))
    print("", flush=True)
    print(f"Processing {index}/{total}: {name}", flush=True)
    print(f"{bar(frac)} {pct}%", flush=True)
    print("-" * 50, flush=True)


def list_images(image: str | None, image_dir: str | None) -> list[Path]:
    if image and image_dir:
        raise ValueError("Use only one of --image or --image-dir")
    if image:
        path = Path(image)
        if not path.exists():
            raise FileNotFoundError(path)
        return [path]
    if not image_dir:
        raise ValueError("Provide --image or --image-dir")
    folder = Path(image_dir)
    images = sorted(
        p for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() in {".tif", ".tiff"}
        and "mesma" not in p.name.lower()
    )
    return images


def has_output(image_path: Path) -> bool:
    return any(image_path.parent.glob(f"{image_path.stem}_mesma_*"))


def main() -> None:
    parser = argparse.ArgumentParser(description="MESMA runner with progress bars")
    parser.add_argument("--library", required=True)
    parser.add_argument("--class-name", default="Type")
    parser.add_argument("--image", default=None)
    parser.add_argument("--image-dir", default=None)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    images = list_images(args.image, args.image_dir)
    if not images:
        print("No images found.", flush=True)
        return

    setup_qgis_paths()
    import qgis  # noqa: F401
    from mesma.interfaces.imports import import_image
    from mesma.interfaces.mesma_cli import create_parser, run_mesma

    total = len(images)
    print(f"Found {total} image(s).", flush=True)
    t0 = time.time()
    ok = skipped = 0
    failed = []

    for i, image_path in enumerate(images, start=1):
        show_progress(i, total, image_path.name)

        if args.skip_existing and has_output(image_path):
            print(f"Skipping existing outputs: {image_path.name}", flush=True)
            skipped += 1
            continue

        mesma_parser = create_parser()
        mesma_args = mesma_parser.parse_args(
            [args.library, args.class_name, str(image_path)]
        )
        try:
            print("Loading image...", flush=True)
            img = import_image(mesma_args.image)
            mesma_args.reflectance_scale_image = float(np.nanmax(img))
            print("Running MESMA (this can take a while for a full tile)...", flush=True)
            run_mesma(mesma_args)
            ok += 1
            print(f"Finished: {image_path.name}", flush=True)
        except Exception as exc:
            failed.append((image_path.name, str(exc)))
            print(f"FAILED: {image_path.name}\n  {exc}", flush=True)

    elapsed_min = (time.time() - t0) / 60.0
    print("", flush=True)
    print("=" * 50, flush=True)
    print(
        f"Done. success={ok} skipped={skipped} failed={len(failed)} total={total}",
        flush=True,
    )
    print(f"Elapsed: {elapsed_min:.1f} min", flush=True)
    for name, err in failed:
        print(f" - {name}: {err}", flush=True)
    show_progress(total, total, "ALL COMPLETE")


if __name__ == "__main__":
    main()
