# Train a Harari voice on an Apple Silicon Mac

One model per reader (`male01`, `female01`). Each starts from Meta's Amharic MMS voice
(`facebook/mms-tts-amh`, same Ge'ez script) and is fine-tuned on that reader's recordings with the
[finetune-hf-vits](https://github.com/ylacombe/finetune-hf-vits) recipe, on the Mac's GPU (MPS).

## 1. Install (one time)

```sh
xcode-select --install            # compilers, if you don't have them
cd harari-language-ai-train
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/check_setup.py --text docs/sentences.txt
```

`check_setup.py` confirms the Apple GPU is visible and reports whether the base model can read
every character in your sentence list. If it lists missing characters, those letters would be
silently dropped — fix that before training (ask Claude to extend the vocabulary).

## 2. Get a reader's recordings

In Google Drive, download the `Harari Voice Recordings/male01` folder, unzip it to
`recordings/male01` (it contains `metadata.csv` and `wavs/`). Then:

```sh
python scripts/prepare_dataset.py --src recordings/male01 --out data/male01
```

This resamples to 16 kHz, evens out loudness, drops clipped / too-short / too-long takes,
splits off a small test set, and writes `data/male01/report.txt` (minutes of usable audio,
character list).

## 3. Train

```sh
bash scripts/train_mac.sh male01
```

The first run downloads the training recipe, `uroman`, and the Amharic base model, and builds the
alignment module. Training runs in full precision with `PYTORCH_ENABLE_MPS_FALLBACK=1`, so any
operation the Apple GPU can't do falls back to the CPU instead of crashing.

- Watch it and **listen to sample audio as it trains:** `tensorboard --logdir outputs/harari-male01`
- Start with a test run on your first ~100 recordings — it tells you early whether everything works.
- Expect hours, not minutes, for a full run on ~1–2 hours of audio; run it overnight with the Mac plugged in.
  Adjust `num_train_epochs` / `per_device_train_batch_size` in `configs/finetune_harari_template.json`.
- If it's very slow (lots of CPU-fallback warnings) or runs out of memory, lower the batch size to 4,
  or run the same commands on a Colab GPU.

## 4. Use the voice

```sh
python scripts/synthesize.py --model outputs/harari-male01 --text "..." --out line.wav
python scripts/synthesize.py --model outputs/harari-female01 --file my_script.txt --out narration.wav --speed 0.95
```

Have native speakers listen and rate samples; their feedback tells you which sentences or sounds
need more recordings.

## License note

The MMS base checkpoints are **CC BY-NC 4.0 (non-commercial)**. Models fine-tuned from them carry
that restriction — check it before using the voice in monetized videos.
