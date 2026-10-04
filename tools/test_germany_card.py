#!/usr/bin/env python3
"""Germany card controls: separate assets, and the labels the live page uses."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gallery_phase1 as gallery

TEMPLATE = Path(__file__).with_name("gallery_template.html")


def test_assets_stay_empty_until_a_distinct_file_exists() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = root / "assets" / "pretext" / "united-kingdom" / "London"
        folder.mkdir(parents=True)
        stills = {
            "file_16x9": folder / "uk-01-900-16x9.png",
            "file_4x5": folder / "uk-01-900-4x5.png",
            "file_9x16": folder / "uk-01-900-9x16.png",
        }
        for path, payload in (
            (stills["file_16x9"], b"STILL16"),
            (stills["file_4x5"], b"STILL45"),
            (stills["file_9x16"], b"STILL916"),
        ):
            path.write_bytes(payload)
        scene = {
            "entry_id": "UK-01-900",
            "file_16x9": "assets/pretext/united-kingdom/London/uk-01-900-16x9.png",
            "file_4x5": "assets/pretext/united-kingdom/London/uk-01-900-4x5.png",
            "file_9x16": "assets/pretext/united-kingdom/London/uk-01-900-9x16.png",
            "approval_status": "Candidate",
        }
        previous = gallery.ROOT
        gallery.ROOT = root
        try:
            gallery.attach_germany_assets(scene)
            for key, _suffix, _kind in gallery.GERMANY_CAPTURES:
                assert scene[key] is None, key

            (folder / "uk-01-900-night-16x9.png").write_bytes(b"STILL16")
            scene["file_night_4x5"] = scene["file_4x5"]
            (folder / "uk-01-900-motion-10s-4x5.mp4").write_bytes(b"\x89PNG\r\nstill-named-as-video")
            gallery.attach_germany_assets(scene)
            assert scene["file_night_16x9"] is None
            assert scene["file_night_4x5"] is None
            assert scene["file_motion_10s_4x5"] is None

            (folder / "uk-01-900-night-16x9.png").write_bytes(b"NIGHT16")
            (folder / "uk-01-900-night-4x5.png").write_bytes(b"NIGHT45")
            (folder / "uk-01-900-night-9x16.png").write_bytes(b"NIGHT916")
            (folder / "uk-01-900-genuine-daylight-16x9.png").write_bytes(b"DAY16")
            (folder / "uk-01-900-genuine-daylight-4x5.png").write_bytes(b"DAY45")
            (folder / "uk-01-900-genuine-daylight-9x16.png").write_bytes(b"DAY916")
            (folder / "uk-01-900-postcard-16x9.png").write_bytes(b"POST16")
            (folder / "uk-01-900-postcard-4x5.png").write_bytes(b"POST45")
            (folder / "uk-01-900-postcard-9x16.png").write_bytes(b"POST916")
            (folder / "uk-01-900-motion-10s-4x5.mp4").write_bytes(b"\x00\x00\x00\x18ftypisom")
            gallery.attach_germany_assets(scene)
            assert scene["file_night_16x9"].endswith("uk-01-900-night-16x9.png")
            assert scene["file_genuine_daylight_16x9"].endswith("genuine-daylight-16x9.png")
            assert scene["file_16x9_postcard"].endswith("postcard-16x9.png")
            assert scene["file_motion_10s_4x5"].endswith("motion-10s-4x5.mp4")
            assert scene["approval_status"] == "Candidate"
            for key in ("file_16x9", "file_4x5", "file_9x16"):
                assert scene[key].endswith(Path(stills[key]).name)
        finally:
            gallery.ROOT = previous


def _page(scenes: list[dict]) -> str:
    html = TEMPLATE.read_text()
    compact = (",", ":")
    payload = json.dumps(scenes, ensure_ascii=False, separators=compact).replace("<", "\\u003c")
    return (
        html.replace("__SCENES__", payload)
        .replace("__UK_META__", "{}")
        .replace("__WOTD_JSON__", "[]")
        .replace("__NARR_JSON__", "{}")
        .replace("__SOCIAL_IMAGE__", '<meta name="twitter:card" content="summary"/>')
    )


def _scene(entry_id: str, **extra) -> dict:
    scene = {
        "entry_id": entry_id,
        "region": "England",
        "city": "London",
        "caption": entry_id,
        "scenario_label": "1 October 2026 · 21:00 Europe/London",
        "composition": "test",
        "description": "",
        "approval_status": "Candidate",
        "format_16x9_approval_status": "Candidate",
        "format_4x5_approval_status": "Candidate",
        "format_9x16_approval_status": "Approved",
        "file_16x9": f"stills/{entry_id}-16x9.png",
        "file_4x5": f"stills/{entry_id}-4x5.png",
        "file_9x16": f"stills/{entry_id}-9x16.png",
        "license_anchor": "#license",
        "license_badge": "Free",
        "motion": None,
    }
    scene.update(extra)
    return scene


def test_card_controls_in_the_browser() -> None:
    full = _scene(
        "UK-TEST-ALL",
        file_night_16x9="captures/all-night-16x9.png",
        file_night_4x5="captures/all-night-4x5.png",
        file_night_9x16="captures/all-night-9x16.png",
        file_genuine_daylight_16x9="captures/all-genuine-daylight-16x9.png",
        file_genuine_daylight_4x5="captures/all-genuine-daylight-4x5.png",
        file_genuine_daylight_9x16="captures/all-genuine-daylight-9x16.png",
        file_16x9_postcard="captures/all-postcard-16x9.png",
        file_4x5_postcard="captures/all-postcard-4x5.png",
        file_9x16_postcard="captures/all-postcard-9x16.png",
        file_motion_10s_4x5="captures/all-motion-10s-4x5.mp4",
    )
    missing = _scene("UK-TEST-NONE")
    probe = """
<script>
(function(){
  function labels(card){
    return Array.prototype.map.call(card.querySelectorAll('.day-row button'), function(b){ return b.textContent; });
  }
  function state(card){
    var img = card.querySelector('img');
    var scenario = card.querySelector('p.scenario');
    var sweep = card.querySelector('.motion-tab');
    return {
      id: card.id,
      labels: labels(card),
      src: img ? img.getAttribute('src') : '',
      scenario: scenario ? scenario.textContent : '',
      video: !!card.querySelector('video.motion-clip'),
      night: !!(card.querySelector('.night-tab.is-active')),
      gday: !!(card.querySelector('.gday-tab.is-active')),
      postcard: !!(card.querySelector('.pc-tab.is-active')),
      sweep: sweep ? sweep.textContent : '',
      download: (card.querySelector('a.download[data-dl="16x9"]') || {}).getAttribute ? card.querySelector('a.download[data-dl="16x9"]').getAttribute('href') : ''
    };
  }
  var cards = Array.prototype.slice.call(document.querySelectorAll('#grid article.card'));
  var full = document.getElementById('UK-TEST-ALL');
  var report = { initial: cards.map(state), daylightOnly: 0 };
  document.querySelectorAll('button').forEach(function(b){
    if (b.textContent.trim() === 'Daylight') report.daylightOnly += 1;
  });
  full.querySelector('.night-tab').click();
  report.afterNight = state(full);
  full.querySelector('.fmt-tab[data-format="4x5"]').click();
  report.night45 = state(full);
  full.querySelector('.gday-tab').click();
  report.afterGday = state(full);
  full.querySelector('.pc-tab').click();
  report.afterPostcard = state(full);
  full.querySelector('.motion-tab').click();
  report.after360 = state(full);
  full.querySelector('.motion-tab').click();
  report.afterClose = state(full);
  var pre = document.createElement('pre');
  pre.id = 'probe';
  pre.textContent = JSON.stringify(report);
  document.body.appendChild(pre);
})();
</script>
"""
    partial = _scene(
        "UK-TEST-PARTIAL",
        file_16x9_postcard="captures/partial-postcard-16x9.png",
        file_motion_10s_4x5="captures/partial-motion-10s-4x5.mp4",
    )
    html = _page([full, missing, partial]).replace("</body>", probe + "\n</body>")
    runner = r"""
const {JSDOM, VirtualConsole} = require('jsdom');
const fs = require('fs');
const virtualConsole = new VirtualConsole();
virtualConsole.forwardTo(console);
const dom = new JSDOM(fs.readFileSync(process.argv[2], 'utf8'), {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://uk.jdvision.org/',
  virtualConsole
});
const probe = dom.window.document.getElementById('probe');
if (!probe) {
  const doc = dom.window.document;
  const grid = doc.getElementById('grid');
  console.error('title', doc.title, 'ids', doc.querySelectorAll('[id]').length, 'grid', !!grid);
  console.error((doc.documentElement.outerHTML || '').slice(0, 300));
  process.exit(1);
}
process.stdout.write(probe.textContent);
"""
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.html"
        page.write_text(html)
        script = Path(tmp) / "run.js"
        script.write_text(runner)
        proc = subprocess.run(
            ["node", str(script), str(page)],
            check=False,
            capture_output=True,
            text=True,
            env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "NODE_PATH": "/tmp/node_modules"},
        )
        if proc.returncode != 0:
            raise SystemExit(proc.stderr[-4000:] + "\n" + proc.stdout[-1000:])
    report = json.loads(proc.stdout)
    assert report["daylightOnly"] == 0
    initial = {row["id"]: row for row in report["initial"]}
    assert initial["UK-TEST-ALL"]["labels"] == [
        "🌙 Night",
        "☀ Genuine daylight",
        "📩 Postcard",
        "▶ 360°",
    ]
    assert initial["UK-TEST-ALL"]["src"] == "captures/all-postcard-16x9.png"
    assert initial["UK-TEST-ALL"]["scenario"] == "Postcard collection"
    assert initial["UK-TEST-ALL"]["postcard"] is True
    assert initial["UK-TEST-ALL"]["night"] is False
    assert initial["UK-TEST-ALL"]["download"] == "captures/all-postcard-16x9.png"
    assert initial["UK-TEST-PARTIAL"]["labels"] == ["📩 Postcard", "▶ 360°"]
    assert "🌙 Night" not in initial["UK-TEST-PARTIAL"]["labels"]
    assert "Genuine daylight" not in " ".join(initial["UK-TEST-PARTIAL"]["labels"])
    assert initial["UK-TEST-NONE"]["labels"] == []
    assert initial["UK-TEST-NONE"]["src"] == "stills/UK-TEST-NONE-16x9.png"
    assert "Scenario:" in initial["UK-TEST-NONE"]["scenario"]
    assert report["afterNight"]["src"] == "captures/all-night-16x9.png"
    assert report["afterNight"]["night"] is True
    assert report["afterNight"]["postcard"] is False
    assert report["afterNight"]["scenario"].startswith("Scenario:")
    assert report["afterNight"]["download"] == "captures/all-night-16x9.png"
    assert report["night45"]["src"] == "captures/all-night-4x5.png"
    assert report["afterGday"]["src"] == "captures/all-genuine-daylight-4x5.png"
    assert report["afterGday"]["gday"] is True
    assert report["afterGday"]["night"] is False
    assert report["afterGday"]["scenario"] == "☀ Genuine daylight capture"
    assert report["afterPostcard"]["src"] == "captures/all-postcard-4x5.png"
    assert report["afterPostcard"]["scenario"] == "Postcard collection"
    assert report["afterPostcard"]["postcard"] is True
    assert report["afterPostcard"]["gday"] is False
    assert report["after360"]["video"] is True
    assert report["after360"]["sweep"] == "✕ Close"
    assert report["afterClose"]["video"] is False
    assert "360°" in report["afterClose"]["sweep"]


if __name__ == "__main__":
    test_assets_stay_empty_until_a_distinct_file_exists()
    test_card_controls_in_the_browser()
    print("germany card controls ok")
