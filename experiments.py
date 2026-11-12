import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from codec.pipeline import Codec, load_grayscale

DEFAULT_IMAGE = Path(__file__).parent / "samples" / "cameraman.png"
DEFAULT_PERCENTS = (20.0, 10.0, 5.0, 2.0, 1.0)
CURVE_PERCENTS = np.geomspace(0.1, 100, 40)
DCT_COLOR = "#2563eb"
DWT_COLOR = "#d97706"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DCT vs Haar DWT compression experiments")
    parser.add_argument("image", nargs="?", default=str(DEFAULT_IMAGE))
    parser.add_argument("--percents", type=float, nargs="+", default=DEFAULT_PERCENTS)
    parser.add_argument("--levels", type=int, default=5)
    parser.add_argument("--crop", type=int, nargs=4, default=(60, 180, 160, 160),
                        metavar=("TOP", "LEFT", "HEIGHT", "WIDTH"))
    parser.add_argument("--out", default="results")
    return parser.parse_args()


def run(codec: Codec, percents) -> list[dict]:
    rows = []
    for percent in percents:
        for result in (codec.dct(percent / 100), codec.dwt(percent / 100)):
            rows.append({
                "method": result.name,
                "target_percent": percent,
                "kept": result.kept,
                "total": result.total,
                "kept_percent": round(100 * result.fraction, 3),
                "ratio": round(result.ratio, 2),
                "psnr_db": round(result.psnr, 2),
                "image": result.image,
            })
    return rows


def save_table(rows: list[dict], path: Path) -> None:
    fields = [key for key in rows[0] if key != "image"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def print_table(rows: list[dict]) -> None:
    print("| Kept, % | Kept coeffs | CR | PSNR DCT, dB | PSNR DWT, dB |")
    print("|---|---|---|---|---|")
    for dct_row, dwt_row in zip(rows[::2], rows[1::2]):
        print(f"| {dct_row['target_percent']:g} | {dct_row['kept']:,} / {dwt_row['kept']:,} "
              f"| {dct_row['ratio']:g} | {dct_row['psnr_db']:.2f} | {dwt_row['psnr_db']:.2f} |")


def save_grid(original: np.ndarray, rows: list[dict], path: Path, crop=None) -> None:
    pairs = list(zip(rows[::2], rows[1::2]))
    window = (slice(None), slice(None))
    if crop:
        top, left, h, w = crop
        window = (slice(top, top + h), slice(left, left + w))
    fig, axes = plt.subplots(len(pairs), 3, figsize=(9, 3 * len(pairs)), squeeze=False)
    for axes_row, (dct_row, dwt_row) in zip(axes, pairs):
        cells = (
            (original, "Original"),
            (dct_row["image"], f"DCT {dct_row['target_percent']:g}%  PSNR {dct_row['psnr_db']:.2f} dB"),
            (dwt_row["image"], f"DWT {dwt_row['target_percent']:g}%  PSNR {dwt_row['psnr_db']:.2f} dB"),
        )
        for ax, (image, title) in zip(axes_row, cells):
            ax.imshow(image[window], cmap="gray", vmin=0, vmax=255, interpolation="nearest")
            ax.set_title(title, fontsize=10)
            ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def save_curve(codec: Codec, percents, path: Path) -> None:
    fractions = CURVE_PERCENTS / 100
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(CURVE_PERCENTS, [codec.dct(f).psnr for f in fractions], color=DCT_COLOR, lw=2, label="DCT 8×8")
    ax.plot(CURVE_PERCENTS, [codec.dwt(f).psnr for f in fractions], color=DWT_COLOR, lw=2,
            label=f"DWT Haar, {codec.levels} levels")
    for percent in percents:
        ax.axvline(percent, color="#9ca3af", lw=0.8, ls="--")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.set_xlabel("Kept coefficients, %")
    ax.set_ylabel("PSNR, dB")
    ax.grid(True, which="both", lw=0.4, alpha=0.6)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    original = load_grayscale(args.image)
    codec = Codec(original, args.levels)
    rows = run(codec, args.percents)
    save_table(rows, out / "results.csv")
    save_grid(original, rows, out / "comparison.png")
    save_grid(original, rows, out / "comparison_crop.png", args.crop)
    save_curve(codec, args.percents, out / "psnr_curve.png")
    print_table(rows)


if __name__ == "__main__":
    main()
