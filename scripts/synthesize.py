#!/usr/bin/env python3
"""Speak Harari text with a trained voice.

    python scripts/synthesize.py --model outputs/harari-male01 --text "..." --out line.wav
    python scripts/synthesize.py --model outputs/harari-female01 --file script.txt --out narration.wav
"""
import argparse
import os
import subprocess

import numpy as np
import soundfile as sf
import torch
from transformers import VitsModel, VitsTokenizer


def uromanize(text, uroman_dir):
    script = os.path.join(uroman_dir, "bin", "uroman.pl")
    out = subprocess.run(["perl", script], input=text.encode(), capture_output=True, check=True)
    return out.stdout.decode().rstrip("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--text")
    ap.add_argument("--file", help="Text file; each line is spoken with a short pause between")
    ap.add_argument("--out", default="out.wav")
    ap.add_argument("--pause", type=float, default=0.4, help="Seconds of silence between lines")
    ap.add_argument("--speed", type=float, default=1.0, help="<1 slower, >1 faster")
    ap.add_argument("--uroman", default=os.environ.get("UROMAN", "third_party/uroman"))
    args = ap.parse_args()

    lines = [args.text] if args.text else [l.strip() for l in open(args.file, encoding="utf-8") if l.strip()]
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    tok = VitsTokenizer.from_pretrained(args.model)
    model = VitsModel.from_pretrained(args.model).to(device).eval()
    model.speaking_rate = 1.0 / args.speed if args.speed else 1.0

    sr = model.config.sampling_rate
    gap = np.zeros(int(sr * args.pause), dtype="float32")
    parts = []
    for line in lines:
        text = uromanize(line, args.uroman) if tok.is_uroman else line
        inputs = tok(text, return_tensors="pt").to(device)
        with torch.no_grad():
            wav = model(**inputs).waveform[0].cpu().numpy().astype("float32")
        parts += [wav, gap]
    sf.write(args.out, np.concatenate(parts[:-1]), sr)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
