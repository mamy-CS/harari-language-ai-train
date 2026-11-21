# Harari Language AI — voice training

Open tools to build a **Harari text-to-speech voice** (ሀረሪ, ISO 639-3 `har`): volunteer readers
record sentences from home, recordings land in Google Drive, and a voice model is fine-tuned on a Mac.

Starting with two voices: **male01** and **female01**, one model each.

## How it fits together

| Step | What | Where |
|---|---|---|
| 1. Sentences | 500–1,000 checked Harari sentences | [`docs/sentences.txt`](docs/sentences.txt), sources in [`texts/`](texts/) |
| 2. Record | Readers use a personal link on phone or laptop; each take uploads automatically | [`docs/`](docs/) (GitHub Pages) + [`apps-script/Code.gs`](apps-script/Code.gs) |
| 3. Prepare | Drive folder → clean 16 kHz dataset with train/test split | [`scripts/prepare_dataset.py`](scripts/prepare_dataset.py) |
| 4. Train | Fine-tune Meta's Amharic MMS voice on the Mac GPU (MPS) | [`scripts/train_mac.sh`](scripts/train_mac.sh) |
| 5. Speak | Turn Harari scripts into voiceovers | [`scripts/synthesize.py`](scripts/synthesize.py) |

## Guides

- [Set up the recording system](guides/setup-recording.md) — Apps Script, GitHub Pages, reader links (~15 min)
- [Reader guide](guides/reader-guide.md) — send this to each reader
- [Training on a Mac](guides/training-on-mac.md)

## Quick start

```sh
# 1. one-time: follow guides/setup-recording.md, add sentences, send links
# 2. when recordings are in: download the Drive folder for a reader to recordings/male01
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python scripts/check_setup.py
python scripts/prepare_dataset.py --src recordings/male01 --out data/male01
bash scripts/train_mac.sh male01
python scripts/synthesize.py --model outputs/harari-male01 --text "..." --out test.wav
```

## Notes

- **Data quality beats quantity:** one consistent reader, quiet room, same mic, 1–3 hours each.
- **Consent:** readers agree to their voice being used to train these models; get it in writing,
  including whether the dataset/model may be published.
- **License:** the MMS base models are CC BY-NC 4.0 (non-commercial), and fine-tuned models inherit that.
- Audio, datasets and model files are git-ignored; they live in Drive and on your Mac.
