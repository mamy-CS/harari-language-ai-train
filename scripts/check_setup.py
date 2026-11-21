#!/usr/bin/env python3
"""Check the Mac is ready to train, and whether the Amharic base model can 'see' all the Harari characters.

    python scripts/check_setup.py --text docs/sentences.txt
"""
import argparse
import os
import sys
from collections import Counter

BASE = "facebook/mms-tts-amh"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="docs/sentences.txt", help="Harari sentences to check against the base vocabulary")
    ap.add_argument("--base", default=BASE)
    args = ap.parse_args()

    import torch
    print(f"PyTorch {torch.__version__}")
    if torch.backends.mps.is_available():
        print("Apple GPU (MPS): available ✓")
    elif torch.cuda.is_available():
        print(f"CUDA GPU: {torch.cuda.get_device_name(0)} ✓")
    else:
        print("No GPU found — training will run on CPU and be very slow.")
    if os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") != "1":
        print("Tip: export PYTORCH_ENABLE_MPS_FALLBACK=1 before training (train_mac.sh does this for you).")

    from transformers import VitsTokenizer
    tok = VitsTokenizer.from_pretrained(args.base)
    print(f"\nBase model: {args.base}")
    print(f"Needs uroman (romanization): {tok.is_uroman}")
    if tok.is_uroman:
        print("  → Text is romanized before training. train_mac.sh downloads uroman and sets UROMAN for you.")

    if not os.path.exists(args.text):
        print(f"\n{args.text} not found — skipping character check.")
        return
    lines = [l.split("\t")[-1].strip() for l in open(args.text, encoding="utf-8") if l.strip() and not l.startswith("#")]
    if not lines:
        print(f"\n{args.text} has no sentences yet — skipping character check.")
        return
    if tok.is_uroman:
        print(f"\n{len(lines)} sentences found. Base model romanizes text, so Ge'ez characters are converted, not dropped.")
        return
    vocab = set(tok.get_vocab())
    counts = Counter(c for l in lines for c in l.lower() if not c.isspace())
    missing = {c: n for c, n in counts.items() if c not in vocab}
    print(f"\n{len(lines)} sentences, {len(counts)} distinct characters.")
    if missing:
        print("Characters NOT in the base vocabulary (they would be dropped):")
        for c, n in sorted(missing.items(), key=lambda x: -x[1]):
            print(f"  {c!r} U+{ord(c):04X}  ×{n}")
    else:
        print("All characters are covered by the base vocabulary ✓")


if __name__ == "__main__":
    sys.exit(main())
