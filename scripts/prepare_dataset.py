#!/usr/bin/env python3
"""Turn one reader's Google Drive folder into a training dataset.

Input  (download the speaker folder from Drive and unzip it):
    recordings/male01/metadata.csv
    recordings/male01/wavs/har_0001.wav ...

Output (a Hugging Face "audiofolder" dataset with train/test splits, 16 kHz mono):
    data/male01/train/metadata.csv + wavs/
    data/male01/test/metadata.csv  + wavs/
    data/male01/report.txt

    python scripts/prepare_dataset.py --src recordings/male01 --out data/male01
"""
import argparse
import csv
import os
import random
from collections import Counter
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def load_mono(path, target_sr):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != target_sr:
        g = gcd(sr, target_sr)
        x = resample_poly(x, target_sr // g, sr // g).astype("float32")
    peak = float(np.abs(x).max()) if x.size else 0.0
    return x, peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Speaker folder with metadata.csv and wavs/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sr", type=int, default=16000, help="MMS models use 16 kHz")
    ap.add_argument("--eval-frac", type=float, default=0.05)
    ap.add_argument("--min-sec", type=float, default=0.8)
    ap.add_argument("--max-sec", type=float, default=20.0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    meta = os.path.join(args.src, "metadata.csv")
    rows = list(csv.DictReader(open(meta, encoding="utf-8")))
    kept, skipped = [], Counter()
    for r in rows:
        src = os.path.join(args.src, r["file_name"])
        text = " ".join(r["text"].split())
        if not os.path.exists(src):
            skipped["missing file"] += 1
            continue
        if not text:
            skipped["empty text"] += 1
            continue
        x, peak = load_mono(src, args.sr)
        dur = len(x) / args.sr
        if dur < args.min_sec or dur > args.max_sec:
            skipped[f"duration outside {args.min_sec}-{args.max_sec}s"] += 1
            continue
        if peak >= 0.999:
            skipped["clipped"] += 1
            continue
        if peak > 0:
            x = x * (0.9 / peak)  # consistent loudness
        kept.append((os.path.basename(r["file_name"]), text, x, dur))

    if not kept:
        raise SystemExit("No usable recordings found.")
    random.Random(args.seed).shuffle(kept)
    n_eval = max(1, int(len(kept) * args.eval_frac)) if len(kept) > 20 else 1
    splits = {"test": kept[:n_eval], "train": kept[n_eval:] or kept[:n_eval]}

    for split, items in splits.items():
        wav_dir = os.path.join(args.out, split, "wavs")
        os.makedirs(wav_dir, exist_ok=True)
        with open(os.path.join(args.out, split, "metadata.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["file_name", "text"])
            for name, text, x, _ in sorted(items):
                sf.write(os.path.join(wav_dir, name), x, args.sr, subtype="PCM_16")
                w.writerow([f"wavs/{name}", text])

    total = sum(k[3] for k in kept)
    chars = Counter(c for k in kept for c in k[1] if not c.isspace())
    report = [
        f"Source: {args.src}",
        f"Usable clips: {len(kept)} of {len(rows)}  ({total/60:.1f} minutes)",
        f"Train: {len(splits['train'])}  Test: {len(splits['test'])}",
        "Skipped: " + (", ".join(f"{k}: {v}" for k, v in skipped.items()) or "none"),
        f"Distinct characters: {len(chars)}",
        "Characters: " + " ".join(c for c, _ in chars.most_common()),
        f"Sample sentence for training previews: {splits['test'][0][1]}",
    ]
    with open(os.path.join(args.out, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
