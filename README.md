# Jason D’s Vision — United Kingdom

AI-generated artistic interpretations of the United Kingdom: England, Scotland, Wales, and Northern Ireland. Free to use, no credit required.

Gallery canon: https://uk.jdvision.org/

GitHub Pages may 404 on that host while TLS finishes. Until the custom domain answers over HTTPS, use https://devlij.github.io/jason-ds-vision-united-kingdom-preview/

`CNAME` (`uk.jdvision.org`) and `.nojekyll` stay in the repo. Do not delete or overwrite them. Do not rewrite DNS if the canon host 404s during provisioning.

All scenes ship as **Candidate** until Cosmo QC. This seed does not approve anything. Scene ids are `UK-01-NNN`. Master files use the prefix `uk-01-NNN`. Timezone is `Europe/London`. Language is English.

## What is here

Phase-1 gallery shell, matching the Spain / Sweden / Ireland A7 page: GA4 `G-PDJ4WSS725`, canonical `https://uk.jdvision.org/`, Open Graph, Twitter card, robots, sitemap, image sitemap, JSON-LD, Union Jack flag band (6px), country switcher with the nine live galleries, then Sweden, then Ireland, then the United Kingdom last and current, word-of-day band, search and region / day-night / mood filters, related scenes, copy-link, lightbox (navigation above the image, controls below, 4 second slideshow), and narration hooks.

The word-of-the-day band is structure only. Its data is an empty array. This seed does not create `word-of-day/en.json` and does not invent English entries. Cosmo supplies the real `en.json` separately.

Cosmo QC approved London scenes UK-01-001 through UK-01-010 on 30 September 2026. Those masters, weather records, hashes, and Approved statuses stay as signed. The published files are the label-bar masters at `assets/pretext/united-kingdom/London/`, the canonical path Cosmo locked.

This branch adds Candidate scenes UK-01-041 through UK-01-050 only. UK-01-011 through UK-01-040 are not in this branch. Nothing new is Approved, and Scotland, Wales, and Northern Ireland are not in this batch. The 30 September late-afternoon retrievals were partly cloudy, WMO code 2 and cloud cover 53%. A daylight aerial is a backfill and no motion file is published.

9:16 masters can sit on disk later. The 9:16 tab and download stay hidden until `format_9x16_approval_status` is set to `Approved` by Jason. Narration controls appear only for Aria or Warm, model `avocado_v2:MAI_01`, status Approved, and an mp3 file. There is no day/night toggle on the card. A motion control is rendered only when a motion file exists. This seed ships no audio.

## Rebuild

```bash
python3 tools/publish_gallery.py
python3 tools/qc_preflight.py
```

`tools/fetch_weather.py` has an empty pin list. Append a United Kingdom viewpoint, timezone `Europe/London`, when a scene is published. Do not invent coordinates here.

`tools/composite_masters.py` bakes the 190px label bar and the five Art. 50 PNG text chunks from a pure pre-text under `assets/pretext/united-kingdom/<City>/`. The Description chunk is: `AI-generated artistic interpretation from the Jason D's Vision United Kingdom gallery. Created with generative AI; not a photograph.`
