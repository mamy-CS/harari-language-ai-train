#!/usr/bin/env bash
# Fine-tune a Harari voice for one reader on an Apple Silicon Mac (Apple GPU / MPS).
#
#   source .venv/bin/activate
#   python scripts/prepare_dataset.py --src recordings/male01 --out data/male01
#   bash scripts/train_mac.sh male01
#
# Starts from Meta's Amharic MMS voice (same Ge'ez script) using the
# finetune-hf-vits recipe: https://github.com/ylacombe/finetune-hf-vits
set -euo pipefail

SPK="${1:?usage: bash scripts/train_mac.sh <speaker_id>   e.g. male01}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
TP="$ROOT/third_party"
mkdir -p "$TP" checkpoints outputs

[ -f "data/$SPK/train/metadata.csv" ] || { echo "Missing data/$SPK — run scripts/prepare_dataset.py first."; exit 1; }

# 1. Training recipe + its fast alignment module (one time)
if [ ! -d "$TP/finetune-hf-vits" ]; then
  git clone --depth 1 https://github.com/ylacombe/finetune-hf-vits "$TP/finetune-hf-vits"
fi
if ! ls "$TP"/finetune-hf-vits/monotonic_align/monotonic_align/core*.so >/dev/null 2>&1; then
  (cd "$TP/finetune-hf-vits/monotonic_align" && mkdir -p monotonic_align && python setup.py build_ext --inplace)
fi

# 2. uroman (romanizer some MMS models need; perl ships with macOS) (one time)
if [ ! -d "$TP/uroman" ]; then
  git clone --depth 1 https://github.com/isi-nlp/uroman "$TP/uroman"
fi
export UROMAN="$TP/uroman"

# 3. Amharic base model with its training discriminator (one time)
if [ ! -d checkpoints/mms-tts-amh-train ]; then
  (cd "$TP/finetune-hf-vits" && python convert_original_discriminator_checkpoint.py \
      --language_code amh --pytorch_dump_folder_path "$ROOT/checkpoints/mms-tts-amh-train")
fi

# 4. Config for this reader
python - "$SPK" "$ROOT" <<'PY'
import json, os, sys
spk, root = sys.argv[1], sys.argv[2]
cfg = json.load(open("configs/finetune_harari_template.json", encoding="utf-8"))
sample = "ሰላም"
for line in open(f"data/{spk}/report.txt", encoding="utf-8"):
    if line.startswith("Sample sentence for training previews:"):
        sample = line.split(":", 1)[1].strip()
for k, v in list(cfg.items()):
    if isinstance(v, str):
        v = v.replace("SPEAKER", spk).replace("SAMPLE_TEXT", sample)
        if v.startswith("./"):
            v = os.path.join(root, v[2:])  # training runs from third_party/, so use absolute paths
        cfg[k] = v
json.dump(cfg, open(f"configs/finetune_harari_{spk}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Wrote configs/finetune_harari_{spk}.json")
PY

# 5. Train on the Apple GPU. Full precision; unsupported GPU ops fall back to CPU.
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false
cd "$TP/finetune-hf-vits"
accelerate launch --num_processes 1 --mixed_precision no \
  run_vits_finetuning.py "$ROOT/configs/finetune_harari_$SPK.json"

echo
echo "Done. Model saved in outputs/harari-$SPK"
echo "Watch progress / listen to samples: tensorboard --logdir outputs/harari-$SPK"
echo "Try it: python scripts/synthesize.py --model outputs/harari-$SPK --text \"...\" --out test.wav"
