# Set up the recording system (one time, ~15 minutes)

Readers open a personal link, record one sentence at a time, and every saved take
uploads straight into your Google Drive. Nothing to install for them.

```
Reader's phone/laptop ──▶ GitHub Pages (docs/index.html) ──▶ Google Apps Script ──▶ Google Drive
                                                                                    Harari Voice Recordings/
                                                                                      male01/   metadata.csv + wavs/
                                                                                      female01/ metadata.csv + wavs/
                                                                                      Harari recordings log (Sheet)
```

## 1. Create the Google Apps Script backend

1. Go to <https://script.google.com> → **New project**. Name it `Harari Voice Recorder`.
2. Delete the sample code, paste in everything from [`apps-script/Code.gs`](../apps-script/Code.gs), and save.
3. In the function dropdown at the top, choose **`setup`** and click **Run**. Approve the
   permission prompt (it needs Drive and Sheets access to save recordings to *your* Drive).
4. Open **Execution log**. It prints the Drive folder link and **one personal link per reader**
   (`male01`, `female01`). Keep these private — anyone with a link can upload as that reader.

## 2. Deploy it as a web app

1. **Deploy → New deployment → ⚙ Select type → Web app**.
2. *Execute as:* **Me**. *Who has access:* **Anyone**.
3. Click **Deploy** and copy the **Web app URL** (ends in `/exec`).

> If you later edit `Code.gs`, use **Deploy → Manage deployments → ✏ Edit → Version: New version**
> so the URL stays the same.

## 3. Connect the page and publish it

1. In this repo, open `docs/config.js` and paste the URL into `APPS_SCRIPT_URL`. Commit.
2. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch →
   Branch: `main`, folder: `/docs`** → Save.
3. After a minute the page is live at `https://mamy-cs.github.io/harari-language-ai-train/`.

## 4. Add the sentences

Put the Harari sentences in `docs/sentences.txt`, one per line (Ge'ez script), and commit.
Once readers have started, **only add new lines at the end** (or give lines fixed IDs —
see the comments in the file) so existing recordings keep matching their sentence.

## 5. Send each reader their link

Send the male reader the `male01` link and the female reader the `female01` link, along with
[the reader guide](reader-guide.md). They can record on a phone or laptop whenever they're free;
progress is kept on the server, so they can switch devices.

## Managing readers

- **Add a reader:** add an ID (e.g. `male02`) to `SPEAKER_IDS` in `Code.gs` and to `SPEAKERS` in
  `docs/config.js`, run `setup` again, and send the new link.
- **Revoke a link:** run `resetLink('male01')` from the editor (e.g. add a one-line function
  `function resetMale(){ resetLink('male01') }` and run it) and send the new link.
- **Check progress:** open the *Harari recordings log* sheet in the Drive folder.

## Getting the data for training

Each speaker folder in Drive is already a dataset (`metadata.csv` + `wavs/`). In Drive,
right-click the `male01` folder → **Download**, unzip into `recordings/male01`, then follow
[training-on-mac.md](training-on-mac.md).
