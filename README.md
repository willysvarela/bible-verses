# Bible Verses Spinner

Swap Claude Code's spinner words ("Bamboozling…", "Percolating…") for random, encouraging Bible
verses, in your language, your Bible version and the themes you care about.

```
✻ Posso todas as coisas naquele que me fortalece — Filipenses 4:13…
  📖 Versículo: “Porque pela graça sois salvos, por meio da fé; …” — Efésios 2:8-9 (ARA)
```

- **Spinner line**: a short verse and its reference, picked at random every turn.
- **Tip line**: the full verse with the version, replacing the built-in tips.
- **Any language and version** served by [bolls.life](https://bolls.life): ARA, NAA, NVT, NTLH, ACF
  (Portuguese), ESV, NLT, NKJV, KJV, WEB (English), RV1960, NTV, LBLA (Spanish) and many more.
- **Themes in your own words**: `encorajamento, pecado, força`, `peace, hope`, `ánimo, gratitud`…
  Twelve built-in themes (encouragement, strength, forgiveness, peace, hope, faith, love, anxiety,
  comfort, gratitude, wisdom, work); for anything else Claude picks fitting references.

Verse text is always fetched from the API in the version you chose, never written from memory.
When a verse is too long for the spinner, Claude picks a short excerpt and the script rejects it
unless it is copied word for word from the verse.

## Install

### As a Claude Code plugin

```bash
claude plugin marketplace add willysvarela/bible-verses
claude plugin install bible-verses@bible-verses
```

Or inside a session: `/plugin install bible-verses --marketplace willysvarela/bible-verses`.

### As a standalone skill

```bash
npx skills add willysvarela/bible-verses
```

## Use

Just ask Claude:

- "Put Bible verses in my spinner, Portuguese, ARA, themes encorajamento, pecado, força"
- "Switch the verses to English, ESV, themes peace and hope"
- "Show my Bible verses setup"
- "Turn off the Bible verses"

It writes `spinnerVerbs` and `spinnerTipsOverride` to your user settings (`~/.claude/settings.json`)
and keeps its state in `~/.claude/bible-verses/`. The spinner verses apply right away; the tip line
loads at the next session. "Turn off" restores exactly the spinner settings you had before. Do that
before uninstalling, since the settings stay after the plugin is gone.

## Requirements

- `python3` (standard library only)
- Internet access when configuring (not while you work)

## Notes

- NIV/NVI is not available in any language: its publisher had bolls.life withdraw it. The skill
  detects this and asks for another version.
- Catholic versions such as CNBB number the Psalms differently, so a built-in Psalm reference may
  land on a neighbouring psalm. Check the samples after configuring.
- Many Bible versions are copyrighted. This project ships only references; the text is fetched
  for your personal display from bolls.life.

## License

MIT
