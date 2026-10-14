---
name: bible-verses
description: Replace Claude Code's spinner words ("Bamboozling…") and spinner tips with random encouraging Bible verses in the user's chosen language, Bible version and themes (e.g. encorajamento, pecado, força). Use when the user wants Bible verses in the spinner, or wants to change the language, version or themes, see the current setup, or turn it off.
---

# Bible verses in the spinner

`scripts/verses.py` fetches verse text from bolls.life and writes two user settings in
`~/.claude/settings.json`:

- `spinnerVerbs` (mode `replace`): the word next to the spinner becomes a short verse plus its reference,
  e.g. `Posso todas as coisas naquele que me fortalece — Filipenses 4:13…`. Claude Code picks one at random each turn.
- `spinnerTipsOverride`: the tip line under the spinner shows the full verse with the version, from
  `~/.claude/bible-verses/tips.json`, with the built-in tips hidden.

**Never write verse text yourself.** All text comes from the API so it matches the chosen version
word for word. You only choose references and, for long verses, excerpts that the script verifies.

Run every command from this skill's directory: `python3 scripts/verses.py <command>`.

## Configure

1. **Collect the three choices** from the user's message; ask only for what is missing.
   - **Language**: the language they want to read in.
   - **Version**: run `translations --lang <language in English, e.g. portuguese>` and offer a few
     well-known ones. Sensible defaults: Portuguese `ARA` (or `NAA`, `NVT`, `NTLH`, `ACF11`), English
     `ESV` (or `NLT`, `NKJV`, `KJV`, `WEB`), Spanish `RV1960` (or `NTV`, `LBLA`). NIV/NVI in any
     language is blocked by its publisher on bolls.life; the script refuses it, so suggest another.
   - **Themes**: any words in any language. Run `themes` to see the built-in themes and their
     aliases (encouragement, strength, forgiveness/sin, peace, hope, faith, love, anxiety/fear, comfort,
     gratitude, wisdom, work). Treat "sin"/"pecado" as forgiveness and grace: the verses stay encouraging.
2. **Map themes.** Built-in themes and aliases resolve automatically. For a theme with no match,
   choose 8–12 encouraging references yourself and pass them with `--extra-refs`, using English
   book names: `"Ps 23:1; John 11:25; Rom 8:28"`.
3. **Apply:**
   ```bash
   python3 scripts/verses.py apply --translation ARA --themes "encorajamento, pecado, força" [--extra-refs "..."] [--display both|spinner|tips]
   ```
   `--display` defaults to `both`. The script remembers the user's previous spinner settings the
   first time, so `off` can restore them.
4. **Excerpts for long verses.** Only verses of up to 72 characters fit the spinner whole. Run
   `long` to get the rest as JSON, then for each pick one contiguous excerpt, **copied character for
   character** from its text, that is encouraging and makes sense alone, 72 characters at most. Never
   pick a fragment that flips the meaning (Ps 73:26 "my flesh and my heart fail" without "God is the
   strength of my heart"); skip a verse instead. Save the list and store it:
   ```bash
   python3 scripts/verses.py excerpts /path/to/excerpts.json   # [{"id": "...", "excerpt": "..."}]
   ```
   The script rejects anything not verbatim, or too long. Retry the rejected ones once.
5. **Report**: version, themes, how many verses are in the spinner and in the tips, and two or three
   samples. Say that the spinner verses apply right away, but the tip line loads its file once per
   process, so it updates in the next session.

## Other requests

- **Show the current setup**: `show`.
- **Change themes or version**: run `apply` again with the new values, then redo the excerpts step
  (excerpts are kept only while the version stays the same).
- **Turn it off**: `off` restores the spinner settings from before the first `apply`.

## Notes

- Psalms numbering differs in Catholic versions (e.g. CNBB uses the Greek numbering), so a built-in
  Psalm reference may land on a neighbouring psalm. For those versions, check the samples after `apply`.
- Book names in references are localized for Portuguese, English and Spanish; other languages use
  the names the version provides.
