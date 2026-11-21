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

To build the reader list, pick clear, natural sentences of 5–15 words, have a fluent speaker
check them, and add them to `docs/sentences.txt`.
