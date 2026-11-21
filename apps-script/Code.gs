/**
 * Harari Voice Recorder — Google Apps Script backend.
 *
 * Saves each recording the readers upload into Google Drive:
 *
 *   Harari Voice Recordings/
 *     male01/   metadata.csv   wavs/har_0001.wav ...
 *     female01/ metadata.csv   wavs/har_0001.wav ...
 *     Harari recordings log   (Google Sheet, one row per take)
 *
 * Each speaker folder is a ready-to-train dataset (metadata.csv + wavs/).
 * Setup steps: guides/setup-recording.md
 */

const ROOT_FOLDER_NAME = 'Harari Voice Recordings';
const SPEAKER_IDS = ['male01', 'female01'];          // add more readers here, then run setup() again
const PAGES_URL = 'https://mamy-cs.github.io/harari-language-ai-train/';
const HEADERS = ['timestamp', 'speaker_id', 'id', 'text', 'duration_sec', 'sample_rate', 'file_id'];

/** Run once from the editor (and again after adding speakers). Prints each reader's personal link. */
function setup() {
  const props = PropertiesService.getScriptProperties();
  const speakers = JSON.parse(props.getProperty('SPEAKERS') || '{}');
  SPEAKER_IDS.forEach(s => { if (!speakers[s]) speakers[s] = Utilities.getUuid().replace(/-/g, '').slice(0, 20); });
  props.setProperty('SPEAKERS', JSON.stringify(speakers));
  const root = getRoot_();
  SPEAKER_IDS.forEach(s => sub_(sub_(root, s), 'wavs'));
  getSheet_();
  Logger.log('Drive folder: ' + root.getUrl());
  Object.keys(speakers).forEach(s => Logger.log(s + ' link: ' + PAGES_URL + '?s=' + s + '&k=' + speakers[s]));
}

/** Run to invalidate one reader's link and print a new one. */
function resetLink(speakerId) {
  const props = PropertiesService.getScriptProperties();
  const speakers = JSON.parse(props.getProperty('SPEAKERS') || '{}');
  speakers[speakerId] = Utilities.getUuid().replace(/-/g, '').slice(0, 20);
  props.setProperty('SPEAKERS', JSON.stringify(speakers));
  Logger.log(speakerId + ' new link: ' + PAGES_URL + '?s=' + speakerId + '&k=' + speakers[speakerId]);
}

/** GET ?s=&k=  → which sentences this reader has already recorded. */
function doGet(e) {
  try {
    const p = e.parameter || {};
    auth_(p.s, p.k);
    const done = rows_().filter(r => r[1] === p.s).map(r => ({ id: String(r[2]), dur: Number(r[4]) || 0 }));
    return json_({ ok: true, done: done });
  } catch (err) {
    return json_({ ok: false, error: String(err.message || err) });
  }
}

/** POST {s,k,id,text,dur,sr,wav(base64)} → saves the WAV and logs it. Re-recording replaces the old take. */
function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const d = JSON.parse(e.postData.contents);
    auth_(d.s, d.k);
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(d.id || '')) throw new Error('Bad sentence id');
    if (!d.wav) throw new Error('No audio');
    const bytes = Utilities.base64Decode(d.wav);
    if (bytes.length > 8 * 1024 * 1024) throw new Error('Recording too large');

    lock.waitLock(30000);
    const spkFolder = sub_(getRoot_(), d.s);
    const wavs = sub_(spkFolder, 'wavs');
    const name = d.id + '.wav';
    const old = wavs.getFilesByName(name);
    while (old.hasNext()) old.next().setTrashed(true);
    const file = wavs.createFile(Utilities.newBlob(bytes, 'audio/wav', name));

    upsert_([new Date(), d.s, d.id, String(d.text || ''), Number(d.dur) || 0, Number(d.sr) || 0, file.getId()]);
    writeMetadata_(d.s, spkFolder);
    return json_({ ok: true, id: d.id });
  } catch (err) {
    return json_({ ok: false, error: String(err.message || err) });
  } finally {
    try { lock.releaseLock(); } catch (x) {}
  }
}

// ---------- helpers ----------
function auth_(s, k) {
  const speakers = JSON.parse(PropertiesService.getScriptProperties().getProperty('SPEAKERS') || '{}');
  if (!s || !k || speakers[s] !== k) throw new Error('Invalid recording link');
}
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function getRoot_() {
  const props = PropertiesService.getScriptProperties();
  const id = props.getProperty('ROOT_ID');
  if (id) { try { return DriveApp.getFolderById(id); } catch (e) {} }
  const f = DriveApp.createFolder(ROOT_FOLDER_NAME);
  props.setProperty('ROOT_ID', f.getId());
  return f;
}
function sub_(parent, name) { const it = parent.getFoldersByName(name); return it.hasNext() ? it.next() : parent.createFolder(name); }
function getSheet_() {
  const props = PropertiesService.getScriptProperties();
  let ss;
  const id = props.getProperty('SHEET_ID');
  if (id) { try { ss = SpreadsheetApp.openById(id); } catch (e) {} }
  if (!ss) {
    ss = SpreadsheetApp.create('Harari recordings log');
    DriveApp.getFileById(ss.getId()).moveTo(getRoot_());
    props.setProperty('SHEET_ID', ss.getId());
    ss.getSheets()[0].setName('recordings').appendRow(HEADERS);
  }
  return ss.getSheetByName('recordings');
}
function rows_() { const sh = getSheet_(); const n = sh.getLastRow(); return n < 2 ? [] : sh.getRange(2, 1, n - 1, HEADERS.length).getValues(); }
function upsert_(row) {
  const sh = getSheet_(); const rows = rows_();
  for (let i = 0; i < rows.length; i++) {
    if (rows[i][1] === row[1] && String(rows[i][2]) === row[2]) { sh.getRange(i + 2, 1, 1, row.length).setValues([row]); return; }
  }
  sh.appendRow(row);
}
function csv_(v) { const s = String(v); return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
function writeMetadata_(speaker, folder) {
  const lines = ['file_name,text,speaker_id,duration_sec'];
  rows_().filter(r => r[1] === speaker)
    .sort((a, b) => String(a[2]).localeCompare(String(b[2])))
    .forEach(r => lines.push([csv_('wavs/' + r[2] + '.wav'), csv_(r[3]), csv_(r[1]), Number(r[4]).toFixed(2)].join(',')));
  const content = lines.join('\n') + '\n';
  const it = folder.getFilesByName('metadata.csv');
  if (it.hasNext()) it.next().setContent(content);
  else folder.createFile('metadata.csv', content, 'text/csv');
}
