"""
Create small web copies of the Round 1 images.

The originals in static/round1 are up to 2048x2048 PNGs (~370 MB in total), far too heavy to
send to every player's browser, and their file names reveal the answer ("..._Past.png").
This writes static/round1_web/<item_id>.webp (max 480 px, ~20-40 KB each). The API serves
these instead of the originals (the originals and the database are left untouched).

Run from the backend folder:   python optimize_round1_images.py
Safe to re-run; existing up-to-date files are skipped.
"""
import csv
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
MANIFEST = BASE_DIR / "round1_manifest.csv"
SOURCE_DIR = BASE_DIR / "static" / "round1"
OUTPUT_DIR = BASE_DIR / "static" / "round1_web"

MAX_SIDE = 480
QUALITY = 82


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    converted = skipped = 0
    missing = []
    before = after = 0

    with open(MANIFEST, "r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            item_id = int(row["item_id"])
            source = SOURCE_DIR / row["image_filename"].strip()
            target = OUTPUT_DIR / f"{item_id}.webp"

            if not source.is_file():
                missing.append(source.name)
                continue

            before += source.stat().st_size

            if target.is_file() and target.stat().st_mtime >= source.stat().st_mtime:
                skipped += 1
                after += target.stat().st_size
                continue

            with Image.open(source) as image:
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
                image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
                image.save(target, "WEBP", quality=QUALITY, method=6)

            after += target.stat().st_size
            converted += 1

    print(f"Converted: {converted}  Skipped (up to date): {skipped}  Missing sources: {len(missing)}")
    for name in missing:
        print("  missing:", name)
    print(f"Size: {before / 1e6:.0f} MB -> {after / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
