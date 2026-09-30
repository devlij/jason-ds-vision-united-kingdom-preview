#!/usr/bin/env python3
"""QC pre-flight for the United Kingdom gallery shell. Exits non-zero on any failure.

The seed ships no scenes, no masters, and no word-of-the-day entries.
Scene-batch checks run only when EXPECTED_IDS is filled in a later stills commit.
Cosmo supplies word-of-day/en.json separately. This shell must not invent it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composite_masters import CANVAS, DESCRIPTION, assert_art50

ROOT = Path(__file__).resolve().parents[1]
ART50_DESCRIPTION = (
    "AI-generated artistic interpretation from the Jason D's Vision United Kingdom gallery. "
    "Created with generative AI; not a photograph."
)
# Empty until a stills commit names the scenes it actually published.
EXPECTED_IDS: list[str] = []
FORBIDDEN = (
    "real-time conditions",
    "photograph of",
    "captured on",
)
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".mp3", ".mp4", ".webm"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def check_note(errors: list[str], entry_id: str, candidate: bool) -> str:
    note_path = ROOT / "approvals" / f"{entry_id}.md"
    if not note_path.is_file():
        errors.append(f"missing approvals/{entry_id}.md")
        return ""
    text = note_path.read_text()
    if candidate:
        if "approval_status: Candidate" not in text:
            errors.append(f"{entry_id} approval note is not Candidate")
        if "approval_status: Approved" in text:
            errors.append(f"{entry_id} approval note self-approved")
    low = text.lower()
    for phrase in FORBIDDEN:
        if phrase in low:
            errors.append(f"{entry_id} approval note contains {phrase!r}")
    if "not a verified on-site observation" not in text:
        errors.append(f"{entry_id} approval note missing model-data wording")
    if "Model data from Open-Meteo, retrieved" not in text:
        errors.append(f"{entry_id} approval note missing retrieval wording")
    return text


def check_weather(errors: list[str], entry_id: str, stamps: set[str]) -> dict | None:
    path = ROOT / "evidence" / "weather" / f"{entry_id}.json"
    if not path.is_file():
        errors.append(f"missing weather {entry_id}")
        return None
    weather = json.loads(path.read_text())
    if weather.get("timezone") != "Europe/London":
        errors.append(f"{entry_id} weather timezone is not Europe/London")
    stamp = weather.get("retrieval_timestamp") or ""
    if stamp in stamps:
        errors.append(f"{entry_id} retrieval second collided: {stamp}")
    stamps.add(stamp)
    hour = stamp[11:13]
    scenario = weather.get("scenario_label") or ""
    if "·" not in scenario or not scenario.split("·", 1)[1].strip().startswith(hour):
        errors.append(f"{entry_id} scenario hour is outside the retrieval hour")
    if (weather.get("model_valid_hour_start") or "")[11:13] != hour:
        errors.append(f"{entry_id} model-valid hour does not contain the scenario hour")
    return weather


def check_masters(errors: list[str], scene: dict, note: str) -> None:
    entry_id = scene.get("entry_id") or ""
    city = scene.get("folder") or scene.get("city") or ""
    for fmt, size in CANVAS.items():
        path = ROOT / "assets" / "united-kingdom" / city / f"{entry_id.lower()}-{fmt}.png"
        if not path.is_file():
            errors.append(f"missing master {path}")
            continue
        with Image.open(path) as im:
            if im.size != size:
                errors.append(f"bad size {path.name} {im.size}")
        try:
            assert_art50(path)
        except SystemExit as err:
            errors.append(str(err))
        if note and sha256(path) not in note:
            errors.append(f"{entry_id} approval note missing sha256 for {fmt}")


def main() -> None:
    errors: list[str] = []
    if DESCRIPTION != ART50_DESCRIPTION:
        errors.append("Art. 50 Description is not the United Kingdom gallery sentence")

    data = json.loads((ROOT / "data.json").read_text())
    if data.get("country") != "United Kingdom" or data.get("code") != "UK":
        errors.append("data.json country/code is not United Kingdom/UK")
    if data.get("canonical") != "https://uk.jdvision.org/":
        errors.append("data.json canonical is not the United Kingdom canon")
    if data.get("ga") != "G-PDJ4WSS725":
        errors.append("data.json GA4 id is not G-PDJ4WSS725")
    if data.get("timezone") != "Europe/London":
        errors.append("data.json timezone is not Europe/London")
    if data.get("lang") != "English":
        errors.append("data.json lang is not English")
    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        errors.append("data.json scenes is not a list")
        scenes = []
    ids = [scene.get("entry_id") for scene in scenes]
    if ids != EXPECTED_IDS:
        errors.append(f"data.json scene order is {ids}")
    by_id = {scene.get("entry_id"): scene for scene in scenes}
    for scene in scenes:
        if scene.get("approval_status") == "Approved":
            errors.append(f"{scene.get('entry_id')} is self-approved")
        for key in (
            "format_16x9_approval_status",
            "format_4x5_approval_status",
            "format_9x16_approval_status",
        ):
            if scene.get(key) == "Approved":
                errors.append(f"{scene.get('entry_id')} {key} is self-approved")

    for invented in (
        ROOT / "word-of-day" / "en.json",
        ROOT / "tools" / "en.json",
        ROOT / "tools" / "uk.json",
    ):
        if invented.exists():
            errors.append(f"do not invent {invented.relative_to(ROOT)}; Cosmo supplies word-of-day/en.json")

    cname_bytes = (ROOT / "CNAME").read_bytes()
    if cname_bytes != b"uk.jdvision.org\n":
        errors.append(f"CNAME bytes changed: {cname_bytes!r}")
    if (ROOT / ".nojekyll").read_bytes() != b"":
        errors.append(".nojekyll is not the empty Pages marker")
    if not (ROOT / ".nojekyll").is_file():
        errors.append(".nojekyll is missing")

    if not EXPECTED_IDS:
        media = [
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES and ".git" not in path.parts
        ]
        if media:
            errors.append("shell seed must not ship masters or audio: " + ", ".join(media))
    else:
        stamps: set[str] = set()
        for entry_id in EXPECTED_IDS:
            scene = by_id.get(entry_id) or {}
            note = check_note(errors, entry_id, candidate=scene.get("approval_status") != "Approved")
            check_weather(errors, entry_id, stamps)
            check_masters(errors, scene, note)

    html = (ROOT / "index.html").read_text() if (ROOT / "index.html").is_file() else ""
    if not html:
        errors.append("missing index.html")
    else:
        if "Download 9:16" in html.split("const SCENES")[0]:
            errors.append("static markup exposes a 9:16 download")
        if ">United Kingdom<" not in html or 'aria-current="page"' not in html:
            errors.append("United Kingdom is not marked current")
        if "flag-uk" not in html:
            errors.append("United Kingdom flag chip is missing")
        if 'id="wotd-data">[]</script>' not in html:
            errors.append("word-of-the-day band is not an empty array")
        if "word-of-day/en.json" in html:
            errors.append("page must not point at an invented English word list")
        if "G-PDJ4WSS725" not in html:
            errors.append("GA4 id missing")
        if html.count("G-PDJ4WSS725") < 2:
            errors.append("GA4 snippet is incomplete")
        if "G-" in html.replace("G-PDJ4WSS725", ""):
            errors.append("a second GA4 id is present")
        if "var INTERVAL=4000;" not in html:
            errors.append("lightbox interval is not 4000ms")
        if "https://uk.jdvision.org/" not in html:
            errors.append("United Kingdom canonical missing")
        if "const SCENES = [];" not in html:
            errors.append("index.html is not an empty scene list")
        if "avocado_v2:MAI_01" not in html:
            errors.append("narration hook is missing")
        if '"src":' in html.split('id="narr-manifest"', 1)[-1][:800]:
            errors.append("narration manifest is not empty")
        for entry_id in EXPECTED_IDS:
            if entry_id not in html:
                errors.append(f"{entry_id} missing from index.html")

    robots = (ROOT / "robots.txt").read_text() if (ROOT / "robots.txt").is_file() else ""
    if "Sitemap: https://uk.jdvision.org/sitemap.xml" not in robots:
        errors.append("robots.txt sitemap is not the United Kingdom canon")
    if "Sitemap: https://uk.jdvision.org/image-sitemap.xml" not in robots:
        errors.append("robots.txt image sitemap is not the United Kingdom canon")
    image_sitemap = (ROOT / "image-sitemap.xml").read_text() if (ROOT / "image-sitemap.xml").is_file() else ""
    if "<image:image>" in image_sitemap:
        errors.append("image sitemap lists an image before any scene is approved")
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"{len(errors)} qc failures")
    print("qc preflight ok")


if __name__ == "__main__":
    main()
