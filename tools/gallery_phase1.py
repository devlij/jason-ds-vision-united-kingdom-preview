"""Phase-1 gallery metadata for the United Kingdom page.

Spain stores each scene as a five-field client tuple:

    [region, "day"|"night", "coastal,mountain,urban,historic", thumbPath, caption]

Filters and related-scene thumbnails read that tuple. Related order is:
same region first, then most shared mood tags, then entry id.

Day or night comes from the scene's own Open-Meteo ``is_day`` flag.
A thumbnail is emitted only when that master file exists.

This seed publishes zero scenes. The word-of-the-day band is structure
only. Cosmo supplies ``word-of-day/en.json`` separately. This shell does
not invent English entries and does not ship that file.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "tools" / "gallery_template.html"
DATA = ROOT / "data.json"
CANON = "https://uk.jdvision.org/"

MOOD_ORDER = ("coastal", "mountain", "urban", "historic")


def master_exists(rel: str | None) -> bool:
    if not rel or not isinstance(rel, str):
        return False
    if rel.startswith("/") or ".." in Path(rel).parts:
        return False
    path = ROOT / rel
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    return path.is_file()


def time_of_day(entry_id: str, scene: dict) -> str:
    path = ROOT / "evidence" / "weather" / f"{entry_id}.json"
    if path.is_file():
        weather = json.loads(path.read_text())
        is_day = weather.get("is_day")
        if is_day == 1:
            return "day"
        if is_day == 0:
            return "night"
        sunrise = weather.get("sunrise") or ""
        stamp = weather.get("retrieval_timestamp") or ""
        if sunrise and stamp and stamp[11:16] < sunrise[11:16]:
            return "night"
    return "night" if scene.get("daynight") == "night" else "day"


def prepare_scene(scene: dict) -> dict | None:
    out = dict(scene)
    if out.get("motion") and not master_exists(out.get("motion")):
        out["motion"] = None
    if out.get("file_9x16") and not master_exists(out.get("file_9x16")):
        out.pop("file_9x16", None)
    if out.get("file_4x5") and not master_exists(out.get("file_4x5")):
        out.pop("file_4x5", None)
    if not master_exists(out.get("file_16x9")):
        return None
    # 9:16 stays on disk. The tab and download render only after Jason clears it.
    if out.get("format_9x16_approval_status") != "Approved":
        out["format_9x16_approval_status"] = out.get("format_9x16_approval_status") or "Candidate"
    return out


def derive_moods(scene: dict) -> list[str]:
    explicit = scene.get("moods")
    if isinstance(explicit, list):
        allowed = set(MOOD_ORDER)
        return [mood for mood in MOOD_ORDER if mood in explicit and mood in allowed]
    return []


def build_meta(scenes: list[dict]) -> dict[str, list]:
    meta: dict[str, list] = {}
    for scene in scenes:
        entry_id = scene.get("entry_id")
        if not entry_id:
            continue
        thumb = scene["file_16x9"]
        if not master_exists(thumb):
            continue
        meta[entry_id] = [
            scene.get("region") or "",
            time_of_day(entry_id, scene),
            ",".join(derive_moods(scene)),
            thumb,
            scene.get("caption") or entry_id,
        ]
    return meta


def load_scenes() -> list[dict]:
    payload = json.loads(DATA.read_text())
    rows = payload["scenes"] if isinstance(payload, dict) else payload
    prepared = []
    for scene in rows:
        item = prepare_scene(scene)
        if item is None:
            print("skip gallery card, missing 16:9 master", scene.get("entry_id"))
            continue
        prepared.append(item)
    return prepared


def load_wotd() -> list:
    """Empty band. Cosmo owns word-of-day/en.json and supplies the entries.

    Do not read or invent an English word list from this shell.
    """
    invented = [
        ROOT / "word-of-day" / "en.json",
        ROOT / "tools" / "en.json",
        ROOT / "tools" / "uk.json",
    ]
    for path in invented:
        if path.is_file() and path.stat().st_size > 0:
            raise SystemExit(
                f"{path.relative_to(ROOT)} must not be invented here. "
                "Cosmo supplies word-of-day/en.json separately."
            )
    return []


def narr_manifest(scenes: list[dict]) -> dict:
    """Only Aria/Warm, avocado_v2:MAI_01, Approved, and a real mp3 are listed."""
    out = {}
    for scene in scenes:
        rec = scene.get("narration")
        if not isinstance(rec, dict):
            continue
        src = rec.get("src") or ""
        if rec.get("status") != "Approved":
            continue
        if rec.get("voice") not in ("Aria", "Warm"):
            continue
        if rec.get("model") != "avocado_v2:MAI_01":
            continue
        if not src.lower().endswith(".mp3") or not master_exists(src):
            continue
        out[scene["entry_id"]] = {
            "src": src,
            "voice": rec["voice"],
            "model": rec["model"],
            "status": "Approved",
        }
    return out


def social_image_meta(scenes: list[dict]) -> str:
    """OG and Twitter image tags only when a 16:9 master is actually published."""
    rel = ""
    for scene in scenes:
        candidate = scene.get("file_16x9") or ""
        if candidate and master_exists(candidate):
            rel = candidate
            break
    if not rel:
        return '<meta name="twitter:card" content="summary"/>'
    url = CANON + rel
    return (
        f'<meta property="og:image" content="{url}"/>\n'
        '<meta name="twitter:card" content="summary_large_image"/>\n'
        f'<meta name="twitter:image" content="{url}"/>'
    )


def _check_meta(meta: dict[str, list]) -> None:
    for entry_id, row in meta.items():
        if len(row) != 5:
            raise SystemExit(f"phase-1 meta for {entry_id} is not a 5-field tuple")
        if row[1] not in ("day", "night"):
            raise SystemExit(f"phase-1 time of day for {entry_id} is {row[1]!r}")
        moods = [part for part in row[2].split(",") if part]
        if any(mood not in MOOD_ORDER for mood in moods):
            raise SystemExit(f"phase-1 mood outside Spain's set for {entry_id}: {row[2]!r}")
        if not master_exists(row[3]):
            raise SystemExit(f"phase-1 thumbnail missing on disk for {entry_id}: {row[3]}")


def _assert_home_link(nav: str) -> None:
    """Keep the Home control first in the switcher so a rebuild cannot drop it."""
    home = '<a class="home-link" href="https://jdvision.org/">&#8962; Home</a>'
    inner = nav.split(">", 1)[1] if ">" in nav else ""
    if not inner.lstrip().startswith(home):
        raise SystemExit("home link must be the first country-switch item and point at https://jdvision.org/")
    between = inner.lstrip()[len(home):inner.lstrip().find('href="https://germany.jdvision.org/"')]
    if between.count('<span class="sep"') != 1:
        raise SystemExit("home link must be followed by the switcher separator")


def assert_phase1(html: str, meta: dict[str, list]) -> None:
    required = (
        'id="f-daynight"',
        'id="f-mood"',
        "Coastal",
        "Mountain",
        "Urban",
        "Historic",
        'id="result-count"',
        'id="clear"',
        "f-daynight').value = ''",
        "f-mood').value = ''",
        "card.id = s.entry_id",
        "function relatedFor",
        "Copy link",
        "Copied",
        "G-PDJ4WSS725",
        "https://spain.jdvision.org/",
        "https://sweden.jdvision.org/",
        "https://uk.jdvision.org/",
        "https://devlij.github.io/jason-ds-vision-ireland-preview/",
        "https://devlij.github.io/jason-ds-vision-netherlands-preview/",
        'id="wotd"',
        "lb-play",
        "Play slideshow",
        "approval_status",
        "flag-band",
        "linear-gradient(to bottom,transparent 33%,#ffffff 33%,#ffffff 66%,transparent 66%),linear-gradient(to right,transparent 44%,#ffffff 44%,#ffffff 56%,transparent 44%),linear-gradient(to bottom,transparent 42%,#C8102E 42%,#C8102E 58%,transparent 58%),linear-gradient(to right,transparent 47.5%,#C8102E 47.5%,#C8102E 52.5%,transparent 52.5%),#012169",
        "flag-uk",
        'viewBox="0 0 60 36"',
        'fill="#012169"',
        'stroke="#C8102E"',
        "format_9x16_approval_status",
        "phase1Enhance",
        'class="home-link"',
        'href="https://jdvision.org/"',
        ".home-link{font-weight:700}",
        "&#8962; Home",
        "getAttribute",
        "avocado_v2:MAI_01",
        "lbFormat",
        "https://jdvision.org/transparency.html",
        'lang="en"',
        "Word of the day",
        "--bg:#0b1220",
        "--card:#111a2c",
        "--text:#eef2f7",
        "--muted:#9db0c6",
        "--accent:#d43a52",
        "--line:#26394f",
    )
    missing = [token for token in required if token not in html]
    if missing:
        raise SystemExit("gallery page is missing Phase-1 or chrome: " + ", ".join(missing))
    if any(token in html for token in ("__SCENES__", "__UK_META__", "__WOTD_JSON__", "__NARR_JSON__", "__SOCIAL_IMAGE__")):
        raise SystemExit("gallery template placeholders were not filled")
    nav_start = html.find('<nav class="country-switch"')
    nav_end = html.find("</nav>", nav_start)
    nav = html[nav_start:nav_end] if nav_start >= 0 else ""
    if nav.count(">United Kingdom<") != 1 or nav.count('aria-current="page"') != 1:
        raise SystemExit("country switcher must mark the United Kingdom once as the current page")
    if "jason-ds-vision-united-kingdom-preview" in nav or "uk.jdvision.org" in nav:
        raise SystemExit("country switcher must not link this page to itself")
    current = nav[nav.find('aria-current="page"') :]
    if "United Kingdom" not in current or "flag-uk" not in current:
        raise SystemExit("aria-current page is not the United Kingdom chip")
    if nav.find(">United Kingdom<") < nav.find(">Ireland<") or nav.find(">Ireland<") < nav.find(">Sweden<"):
        raise SystemExit("United Kingdom must be last, after Ireland and Sweden")
    order = [
        "Germany",
        "Italy",
        "France",
        "Greece",
        "Spain",
        "Norway",
        "Denmark",
        "Switzerland",
        "Netherlands",
        "Finland",
        "Sweden",
        "Ireland",
        "United Kingdom",
    ]
    positions = [nav.find(name) for name in order]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        raise SystemExit(f"switcher order is not Germany→United Kingdom: {positions}")
    _assert_home_link(nav)
    if "linear-gradient(#fff,#fff) center/45% 22%" not in html:
        raise SystemExit("Swiss flag chip is missing the white cross")
    if not meta:
        if "const SCENES = [];" not in html:
            raise SystemExit("empty gallery must publish an empty SCENES array")
        return
    for entry_id, row in meta.items():
        if entry_id not in html:
            raise SystemExit(f"{entry_id} missing from generated page")
        if row[3] not in html:
            raise SystemExit(f"thumbnail for {entry_id} missing from generated page")


def render_gallery(scenes: list[dict] | None = None) -> str:
    page_scenes = scenes if scenes is not None else load_scenes()
    meta = build_meta(page_scenes)
    _check_meta(meta)
    template = TEMPLATE.read_text()
    wotd = load_wotd()
    narr = narr_manifest(page_scenes)
    # Compact separators match the gallery already published on the Sweden main.
    compact = (",", ":")
    payload = json.dumps(page_scenes, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    meta_payload = json.dumps(meta, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    wotd_payload = json.dumps(wotd, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    narr_payload = json.dumps(narr, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    html = (
        template.replace("__SCENES__", payload)
        .replace("__UK_META__", meta_payload)
        .replace("__WOTD_JSON__", wotd_payload)
        .replace("__NARR_JSON__", narr_payload)
        .replace("__SOCIAL_IMAGE__", social_image_meta(page_scenes))
    )
    assert_phase1(html, meta)
    return html
