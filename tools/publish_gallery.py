#!/usr/bin/env python3
"""Write index.html, robots.txt, sitemap.xml, and image-sitemap.xml.

Approved scenes (RPV / Jason-authorized) are listed in image-sitemap.xml.
Candidates contribute nothing. 9:16 is never listed.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from gallery_phase1 import DATA, ROOT, load_scenes, render_gallery, master_exists

SITE = "https://uk.jdvision.org/"


def write_robots() -> None:
    text = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE}sitemap.xml\n"
        f"Sitemap: {SITE}image-sitemap.xml\n"
    )
    (ROOT / "robots.txt").write_text(text)


def write_sitemap() -> None:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE}</loc></url>\n"
        "</urlset>\n"
    )
    (ROOT / "sitemap.xml").write_text(xml)


def _xml_text(value: str) -> str:
    return escape(value, entities={'"': "&quot;", "'": "&apos;"})


def _resolve_master(rel: str) -> str | None:
    if not rel or "9x16" in rel:
        return None
    if master_exists(rel):
        return rel
    if rel.startswith("assets/united-kingdom/"):
        alt = "assets/pretext/united-kingdom/" + rel[len("assets/united-kingdom/") :]
        if master_exists(alt):
            return alt
    return None


def write_image_sitemap(scenes: list[dict]) -> None:
    """Approved scenes only. 9:16 is never listed. Candidates contribute nothing."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    n = 0
    for scene in scenes:
        if scene.get("approval_status") != "Approved":
            continue
        images = []
        for key in ("file_16x9", "file_4x5"):
            rel = _resolve_master(scene.get(key) or "")
            if rel:
                images.append(rel)
        if not images:
            continue
        n += 1
        title = (scene.get("caption") or "").strip()
        caption = (scene.get("description") or scene.get("alt_text") or "").strip()
        city = (scene.get("city") or "").strip()
        country = (scene.get("country") or "").strip()
        geo = f"{city}, {country}" if city and country else (city or country)
        lines.append("  <url>")
        lines.append(f"    <loc>{SITE}#{scene['entry_id']}</loc>")
        for rel in images:
            lines.append("    <image:image>")
            lines.append(f"      <image:loc>{SITE}{rel}</image:loc>")
            lines.append(f"      <image:caption>{_xml_text(caption)}</image:caption>")
            lines.append(f"      <image:title>{_xml_text(title)}</image:title>")
            lines.append(f"      <image:geo_location>{_xml_text(geo)}</image:geo_location>")
            lines.append("    </image:image>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "image-sitemap.xml").write_text("\n".join(lines) + "\n")
    print(f"image-sitemap Approved urls={n}")


def main() -> None:
    scenes = load_scenes()
    html = render_gallery(scenes)
    (ROOT / "index.html").write_text(html)
    write_robots()
    write_sitemap()
    write_image_sitemap(scenes)
    print(f"wrote index.html ({len(html)} bytes), robots.txt, sitemap.xml, image-sitemap.xml")
    print(f"scenes {len(scenes)}")


if __name__ == "__main__":
    main()
