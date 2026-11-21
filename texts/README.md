# Harari texts

Collect Harari writing here — it feeds the reader sentence list and, with translations, helps
Claude (and later a translation model) write better Harari.

```
texts/
  monolingual/   Harari-only text (.txt, UTF-8, Ge'ez script) — books, newsletters, articles
  parallel/      Harari with translations, one passage per line, tab-separated:
                 harari<TAB>english<TAB>amharic   (leave a column empty if missing)
```

Note the source of each file (title, author, year) in a `SOURCES.md` next to it.
Only commit texts you have the right to share; keep copyrighted books out of a public repo.

## Translation drive

`translation/source_sentences.tsv` holds 500 original English sentences (everyday life, Harar and
community life, stories and proverb-style lines, and science-explainer phrasing). Volunteers translate
them in the "Harari sentence translation" Google Sheet; checked rows are imported with
`scripts/import_translations.py`, which writes `docs/sentences.txt` and `parallel/harari_english.tsv`.

To build the reader list by hand instead, pick clear, natural sentences of 5–15 words, have a fluent speaker
check them, and add them to `docs/sentences.txt`.
