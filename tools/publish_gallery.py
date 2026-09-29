#!/usr/bin/env python3
"""Write index.html, robots.txt, sitemap.xml, and image-sitemap.xml.

The United Kingdom seed has no Cosmo approval. This publisher refuses every
Approved status. Scene stills land later as Candidate.
"""

from __future__ import annotations

import json

from gallery_phase1 import DATA, ROOT, load_scenes, render_gallery

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


def write_image_sitemap(scenes: list[dict]) -> None:
    """Approved scenes only. 9:16 is never listed. Candidates contribute nothing."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for scene in scenes:
        if scene.get("approval_status") != "Approved":
            continue
        images = []
        for key in ("file_16x9", "file_4x5"):
            rel = scene.get(key) or ""
            if not rel or "9x16" in rel:
                continue
            images.append(f"    <image:image><image:loc>{SITE}{rel}</image:loc></image:image>")
        if not images:
            continue
        lines.append(f"  <url><loc>{SITE}#{scene['entry_id']}</loc>")
        lines.extend(images)
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "image-sitemap.xml").write_text("\n".join(lines) + "\n")


def refuse_self_approval() -> None:
    payload = json.loads(DATA.read_text())
    rows = payload["scenes"] if isinstance(payload, dict) else payload
    for scene in rows:
        entry_id = scene.get("entry_id")
        if scene.get("approval_status") == "Approved":
            raise SystemExit(f"refusing to publish a self-approved scene: {entry_id}")
        for key in (
            "format_16x9_approval_status",
            "format_4x5_approval_status",
            "format_9x16_approval_status",
        ):
            if scene.get(key) == "Approved":
                raise SystemExit(f"refusing to publish a self-approved format: {entry_id} {key}")


def main() -> None:
    refuse_self_approval()
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
