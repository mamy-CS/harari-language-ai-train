// Recorder settings. After you deploy the Google Apps Script (see guides/setup-recording.md),
// paste its Web app URL below and commit.
window.RECORDER_CONFIG = {
  // Google Apps Script Web app URL, ends with /exec
  APPS_SCRIPT_URL: "PASTE_YOUR_APPS_SCRIPT_WEB_APP_URL_HERE",

  // Sentence list served next to this page. One sentence per line.
  SENTENCES_URL: "sentences.txt",

  // Recording goal per reader, in minutes of clean speech (1–3 hours is a good target).
  GOAL_MINUTES: 120,

  // Shown to readers who open the page without a personal link.
  CONTACT_NAME: "Mohammed",

  // Display names for each reader link (?s=...).
  SPEAKERS: {
    male01: "Male voice",
    female01: "Female voice"
  }
};
