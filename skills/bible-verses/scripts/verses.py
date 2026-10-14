#!/usr/bin/env python3
"""Fill Claude Code's spinner with Bible verses fetched from bolls.life.

  verses.py translations [--lang portuguese]   list available versions
  verses.py themes                             list built-in themes and their aliases
  verses.py apply --translation ARA --themes "encorajamento,pecado,força" [--extra-refs "Ps 23:1; John 11:35"]
                  [--display both|spinner|tips]
  verses.py long                               verses too long for the spinner that still need an excerpt
  verses.py excerpts FILE|-                    store [{"id", "excerpt"}] excerpts, each verbatim from its verse
  verses.py show                               current config and a few sample verses
  verses.py off                                restore the spinner settings from before the first apply

Verse text is always fetched, never written from memory. References use English book names or
abbreviations ("Phil 4:13", "1 John 1:9", "Ps 121:1-2"); Portuguese and Spanish names work too.
"""
import argparse, html, json, os, random, re, sys, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
THEMES_FILE = os.path.join(HERE, "..", "data", "themes.json")
STATE_DIR = os.path.expanduser("~/.claude/bible-verses")
CONFIG_FILE = os.path.join(STATE_DIR, "config.json")
TIPS_FILE = os.path.join(STATE_DIR, "tips.json")
VERSES_FILE = os.path.join(STATE_DIR, "verses.json")
SETTINGS_FILE = os.path.expanduser("~/.claude/settings.json")
API = "https://bolls.life"

MAX_VERB = 72  # spinner line: verb + "…" + timer must fit one terminal row
MAX_TIPS = 200  # Claude Code reads at most 200 tips

# number, English, Portuguese, Spanish, extra aliases
BOOKS = [
    (1, "Genesis", "Gênesis", "Génesis", "gen gn"), (2, "Exodus", "Êxodo", "Éxodo", "exod ex"),
    (3, "Leviticus", "Levítico", "Levítico", "lev lv"), (4, "Numbers", "Números", "Números", "num nm"),
    (5, "Deuteronomy", "Deuteronômio", "Deuteronomio", "deut dt"), (6, "Joshua", "Josué", "Josué", "josh js"),
    (7, "Judges", "Juízes", "Jueces", "judg jz"), (8, "Ruth", "Rute", "Rut", "rt"),
    (9, "1 Samuel", "1 Samuel", "1 Samuel", "1sam 1sm"), (10, "2 Samuel", "2 Samuel", "2 Samuel", "2sam 2sm"),
    (11, "1 Kings", "1 Reis", "1 Reyes", "1kgs 1ki 1rs"), (12, "2 Kings", "2 Reis", "2 Reyes", "2kgs 2ki 2rs"),
    (13, "1 Chronicles", "1 Crônicas", "1 Crónicas", "1chr 1cr"), (14, "2 Chronicles", "2 Crônicas", "2 Crónicas", "2chr 2cr"),
    (15, "Ezra", "Esdras", "Esdras", "ezr ed"), (16, "Nehemiah", "Neemias", "Nehemías", "neh ne"),
    (17, "Esther", "Ester", "Ester", "esth et"), (18, "Job", "Jó", "Job", "jb"),
    (19, "Psalms", "Salmos", "Salmos", "ps psa psalm sl sal"), (20, "Proverbs", "Provérbios", "Proverbios", "prov pv pr"),
    (21, "Ecclesiastes", "Eclesiastes", "Eclesiastés", "eccl ec"), (22, "Song of Songs", "Cânticos", "Cantares", "song ct cnt"),
    (23, "Isaiah", "Isaías", "Isaías", "isa is"), (24, "Jeremiah", "Jeremias", "Jeremías", "jer jr"),
    (25, "Lamentations", "Lamentações", "Lamentaciones", "lam lm"), (26, "Ezekiel", "Ezequiel", "Ezequiel", "ezek ez"),
    (27, "Daniel", "Daniel", "Daniel", "dan dn"), (28, "Hosea", "Oseias", "Oseas", "hos os"),
    (29, "Joel", "Joel", "Joel", "jl"), (30, "Amos", "Amós", "Amós", "am"),
    (31, "Obadiah", "Obadias", "Abdías", "obad ob"), (32, "Jonah", "Jonas", "Jonás", "jon jn"),
    (33, "Micah", "Miqueias", "Miqueas", "mic mq"), (34, "Nahum", "Naum", "Nahúm", "nah na"),
    (35, "Habakkuk", "Habacuque", "Habacuc", "hab hc"), (36, "Zephaniah", "Sofonias", "Sofonías", "zeph sf"),
    (37, "Haggai", "Ageu", "Hageo", "hag ag"), (38, "Zechariah", "Zacarias", "Zacarías", "zech zc"),
    (39, "Malachi", "Malaquias", "Malaquías", "mal ml"), (40, "Matthew", "Mateus", "Mateo", "matt mt"),
    (41, "Mark", "Marcos", "Marcos", "mk mc"), (42, "Luke", "Lucas", "Lucas", "lk lc"),
    (43, "John", "João", "Juan", "jn jo"), (44, "Acts", "Atos", "Hechos", "at hch"),
    (45, "Romans", "Romanos", "Romanos", "rom rm"), (46, "1 Corinthians", "1 Coríntios", "1 Corintios", "1cor 1co"),
    (47, "2 Corinthians", "2 Coríntios", "2 Corintios", "2cor 2co"), (48, "Galatians", "Gálatas", "Gálatas", "gal gl"),
    (49, "Ephesians", "Efésios", "Efesios", "eph ef"), (50, "Philippians", "Filipenses", "Filipenses", "phil fp flp"),
    (51, "Colossians", "Colossenses", "Colosenses", "col cl"), (52, "1 Thessalonians", "1 Tessalonicenses", "1 Tesalonicenses", "1thess 1ts"),
    (53, "2 Thessalonians", "2 Tessalonicenses", "2 Tesalonicenses", "2thess 2ts"), (54, "1 Timothy", "1 Timóteo", "1 Timoteo", "1tim 1tm"),
    (55, "2 Timothy", "2 Timóteo", "2 Timoteo", "2tim 2tm"), (56, "Titus", "Tito", "Tito", "tit tt"),
    (57, "Philemon", "Filemom", "Filemón", "phlm fm"), (58, "Hebrews", "Hebreus", "Hebreos", "heb hb"),
    (59, "James", "Tiago", "Santiago", "jas tg stg"), (60, "1 Peter", "1 Pedro", "1 Pedro", "1pet 1pe"),
    (61, "2 Peter", "2 Pedro", "2 Pedro", "2pet 2pe"), (62, "1 John", "1 João", "1 Juan", "1jn 1jo"),
    (63, "2 John", "2 João", "2 Juan", "2jn 2jo"), (64, "3 John", "3 João", "3 Juan", "3jn 3jo"),
    (65, "Jude", "Judas", "Judas", "jd"), (66, "Revelation", "Apocalipse", "Apocalipsis", "rev ap"),
]
LANG_COL = {"en": 1, "pt": 2, "es": 3}
LABELS = {"en": "📖 Verse", "pt": "📖 Versículo", "es": "📖 Versículo"}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


BOOK_ALIASES = {}
for row in BOOKS:
    for name in row[1:4] + tuple(row[4].split()):
        BOOK_ALIASES.setdefault(norm(name), row[0])


def parse_ref(ref):
    m = re.match(r"^\s*(.+?)\s+(\d+):(\d+)(?:-(\d+))?\s*$", ref)
    if not m:
        raise ValueError(f"bad reference: {ref!r}")
    book = BOOK_ALIASES.get(norm(m.group(1)))
    if not book:
        raise ValueError(f"unknown book in {ref!r}")
    start = int(m.group(3))
    return book, int(m.group(2)), start, int(m.group(4) or start)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "claude-code-bible-verses-skill"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def languages():
    return get_json(f"{API}/static/bolls/app/views/languages.json")


def find_translation(code):
    for lang in languages():
        for t in lang["translations"]:
            if t["short_name"].lower() == code.lower():
                return lang["language"], t
    return None, None


def lang_code(language_name):
    first = language_name.split()[0].lower()
    return {"english": "en", "portuguese": "pt", "português": "pt", "spanish": "es", "español": "es"}.get(first)


def clean(text):
    text = re.sub(r"<S>.*?</S>|<sup>.*?</sup>", "", text)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip("'\"“”‘’«»").strip()


def looks_blocked(text):
    return len(text) > 400 or "http" in text


def verse_key(text):
    return re.sub(r"\s+", " ", text).strip().rstrip(".,;:")


def build_verbs(verses, excerpts):
    """Whole verses that fit the spinner, plus excerpts the skill picked for longer ones."""
    verbs = []
    for v in verses:
        line = excerpts.get(v["id"]) or verse_key(v["text"])
        if len(line) <= MAX_VERB:
            verbs.append(f"{line} — {v['ref']}")
    return verbs


def theme_bank():
    with open(THEMES_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def resolve_themes(words):
    bank = theme_bank()
    lookup = {}
    for key, theme in bank.items():
        for alias in [key] + theme["aliases"]:
            lookup[norm(alias)] = key
    found, unknown = [], []
    for word in words:
        key = lookup.get(norm(word))
        (found if key else unknown).append(key or word)
    return bank, list(dict.fromkeys(found)), unknown


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def cmd_translations(args):
    for lang in languages():
        if args.lang and args.lang.lower() not in lang["language"].lower():
            continue
        print(f"## {lang['language']}")
        for t in lang["translations"]:
            print(f"  {t['short_name']:<10} {t['full_name']}")


def cmd_themes(_args):
    for key, theme in theme_bank().items():
        print(f"{key:<14} {len(theme['refs']):>2} verses  aliases: {', '.join(theme['aliases'])}")


def cmd_apply(args):
    language, translation = find_translation(args.translation)
    if not translation:
        sys.exit(f"Unknown translation {args.translation!r}. Run: verses.py translations --lang <language>")
    code = translation["short_name"]
    lang = args.language or lang_code(language) or "en"

    words = [w.strip() for w in re.split(r"[,;]", args.themes or "") if w.strip()]
    bank, keys, unknown = resolve_themes(words)
    extra = [r.strip() for r in re.split(r";", args.extra_refs or "") if r.strip()]
    if unknown and not extra:
        sys.exit(f"No built-in theme for: {', '.join(unknown)}. Pass --extra-refs with references for them.")
    refs = [r for k in keys for r in bank[k]["refs"]] + extra
    if not refs:
        sys.exit("No themes or references given.")

    parsed = []
    for ref in dict.fromkeys(refs):
        try:
            parsed.append(parse_ref(ref))
        except ValueError as err:
            print(f"skipping: {err}", file=sys.stderr)

    books = {b["bookid"]: b["name"] for b in get_json(f"{API}/get-books/{code}/")}
    chapters = sorted({(b, c) for b, c, _, _ in parsed})

    def fetch(bc):
        try:
            return bc, {v["verse"]: clean(v["text"]) for v in get_json(f"{API}/get-text/{code}/{bc[0]}/{bc[1]}/")}
        except Exception as err:
            print(f"fetch failed for book {bc[0]} chapter {bc[1]}: {err}", file=sys.stderr)
            return bc, {}

    with ThreadPoolExecutor(max_workers=6) as pool:
        text = dict(pool.map(fetch, chapters))

    verses = []
    for book, chapter, start, end in parsed:
        parts = [text.get((book, chapter), {}).get(v) for v in range(start, end + 1)]
        if not all(parts):
            print(f"skipping {book} {chapter}:{start}: not in {code}", file=sys.stderr)
            continue
        body = " ".join(parts)
        if looks_blocked(body):
            sys.exit(f"{code} is not served as verse text by bolls.life (publisher restriction). Pick another version.")
        col = LANG_COL.get(lang)
        name = BOOKS[book - 1][col] if col else books.get(book, BOOKS[book - 1][1])
        ref = f"{name} {chapter}:{start}" + (f"-{end}" if end != start else "")
        verses.append({"id": f"bible-{code}-{book}-{chapter}-{start}-{end}", "ref": ref, "text": body})

    if not verses:
        sys.exit("No verses could be fetched.")
    random.shuffle(verses)

    tips = [{"id": v["id"], "text": f"“{v['text']}” — {v['ref']} ({code})"[:500]} for v in verses[:MAX_TIPS]]
    config = read_json(CONFIG_FILE, {})
    if config.get("translation") != code:
        config["excerpts"] = {}
    excerpts = {k: e for k, e in config.get("excerpts", {}).items() if any(v["id"] == k for v in verses)}
    config["excerpts"] = excerpts
    verbs = build_verbs(verses, excerpts)
    settings = read_json(SETTINGS_FILE, {})
    if "previous" not in config:
        config["previous"] = {k: settings.get(k) for k in ("spinnerVerbs", "spinnerTipsOverride")}
    config.update({
        "translation": code, "translation_name": translation["full_name"], "language": lang,
        "themes": keys, "unmatched_themes": unknown, "extra_refs": extra, "display": args.display,
    })

    write_json(TIPS_FILE, tips)
    write_json(VERSES_FILE, verses)
    def restore(key):
        if config["previous"].get(key) is None:
            settings.pop(key, None)
        else:
            settings[key] = config["previous"][key]

    if args.display in ("both", "spinner") and verbs:
        settings["spinnerVerbs"] = {"mode": "replace", "verbs": verbs}
    else:
        restore("spinnerVerbs")
    if args.display in ("both", "tips"):
        settings["spinnerTipsOverride"] = {"label": LABELS.get(lang, LABELS["en"]), "tipsFile": "~/.claude/bible-verses/tips.json", "excludeDefault": True}
    else:
        restore("spinnerTipsOverride")
    write_json(SETTINGS_FILE, settings)
    write_json(CONFIG_FILE, config)

    print(f"Applied {len(verses)} verses from {code} ({translation['full_name']}), themes: {', '.join(keys + unknown)}")
    print(f"  spinner verbs: {len(verbs) if args.display in ('both', 'spinner') else 0}   tips: {len(tips) if args.display in ('both', 'tips') else 0}")
    if settings.get("spinnerTipsEnabled") is False and args.display in ("both", "tips"):
        print("  note: spinnerTipsEnabled is false, so the tip line stays hidden")
    missing = [v for v in verses if v["id"] not in excerpts and len(verse_key(v["text"])) > MAX_VERB]
    if missing and args.display in ("both", "spinner"):
        print(f"  {len(missing)} verses are too long for the spinner; run `verses.py long` to pick excerpts")


def cmd_long(_args):
    config = read_json(CONFIG_FILE, {})
    excerpts = config.get("excerpts", {})
    verses = read_json(VERSES_FILE, [])
    todo = [{"id": v["id"], "ref": v["ref"], "text": v["text"]} for v in verses
            if v["id"] not in excerpts and len(verse_key(v["text"])) > MAX_VERB]
    print(json.dumps({"max_chars": MAX_VERB, "verses": todo}, indent=2, ensure_ascii=False))


def cmd_excerpts(args):
    """Store spinner excerpts: a JSON list of {"id", "excerpt"}; each must be copied verbatim from its verse."""
    entries = json.load(sys.stdin if args.file == "-" else open(args.file, encoding="utf-8"))
    verses = {v["id"]: v for v in read_json(VERSES_FILE, [])}
    config = read_json(CONFIG_FILE, None)
    if not config or not verses:
        sys.exit("Run `verses.py apply` first.")
    excerpts = config.setdefault("excerpts", {})
    accepted = 0
    for entry in entries:
        verse = verses.get(entry.get("id"))
        excerpt = verse_key(entry.get("excerpt", "")).strip("'\"“”‘’«»")
        if not verse:
            print(f"rejected {entry.get('id')}: unknown id", file=sys.stderr)
        elif not excerpt or excerpt not in verse_key(verse["text"]):
            print(f"rejected {verse['ref']}: excerpt is not verbatim from the verse", file=sys.stderr)
        elif len(excerpt) > MAX_VERB:
            print(f"rejected {verse['ref']}: {len(excerpt)} chars, max {MAX_VERB}", file=sys.stderr)
        else:
            excerpts[verse["id"]] = excerpt
            accepted += 1
    settings = read_json(SETTINGS_FILE, {})
    if config.get("display") in ("both", "spinner"):
        settings["spinnerVerbs"] = {"mode": "replace", "verbs": build_verbs(list(verses.values()), excerpts)}
        write_json(SETTINGS_FILE, settings)
    write_json(CONFIG_FILE, config)
    print(f"Stored {accepted} excerpts; spinner now has {len(settings.get('spinnerVerbs', {}).get('verbs', []))} verses.")


def cmd_show(_args):
    config = read_json(CONFIG_FILE, None)
    if not config:
        print("Not configured yet.")
        return
    print(json.dumps({k: v for k, v in config.items() if k != "previous"}, indent=2, ensure_ascii=False))
    tips = read_json(TIPS_FILE, [])
    for tip in random.sample(tips, min(3, len(tips))):
        print("  " + tip["text"])


def cmd_off(_args):
    config = read_json(CONFIG_FILE, None)
    settings = read_json(SETTINGS_FILE, {})
    previous = (config or {}).get("previous", {})
    for key in ("spinnerVerbs", "spinnerTipsOverride"):
        if previous.get(key) is None:
            settings.pop(key, None)
        else:
            settings[key] = previous[key]
    write_json(SETTINGS_FILE, settings)
    if config:
        os.remove(CONFIG_FILE)
    print("Spinner restored to its previous settings.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("translations"); p.add_argument("--lang"); p.set_defaults(fn=cmd_translations)
    sub.add_parser("themes").set_defaults(fn=cmd_themes)
    p = sub.add_parser("apply")
    p.add_argument("--translation", required=True)
    p.add_argument("--themes", default="")
    p.add_argument("--extra-refs", default="")
    p.add_argument("--language", choices=sorted(LANG_COL), help="book-name language; inferred from the translation")
    p.add_argument("--display", choices=["both", "spinner", "tips"], default="both")
    p.set_defaults(fn=cmd_apply)
    sub.add_parser("long").set_defaults(fn=cmd_long)
    p = sub.add_parser("excerpts"); p.add_argument("file", help="JSON file, or - for stdin"); p.set_defaults(fn=cmd_excerpts)
    sub.add_parser("show").set_defaults(fn=cmd_show)
    sub.add_parser("off").set_defaults(fn=cmd_off)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
