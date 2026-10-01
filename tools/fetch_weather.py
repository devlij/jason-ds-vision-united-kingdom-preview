#!/usr/bin/env python3
"""One fresh Open-Meteo retrieval per scene. Never batch-share a timestamp.

Existing evidence files are kept. The United Kingdom seed list is empty until a still is published.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "weather"
MONTHS = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Later scenes append here. Do not re-list a scene that already has a file.
# Pins are the public viewpoint, not a surveyed tripod mark.
SCENES: list[tuple[str, str, str, float, float, str]] = [
    # All four nations: England, Scotland, Wales, and Northern Ireland.
    # Append one public viewpoint per scene when a still is published.
    # (entry_id, site, city, latitude, longitude, "Europe/London")
    # Pins are the public viewpoint, not a surveyed tripod mark.
    # London morning batch, 30 September 2026. England only; the other nations follow.
    ("UK-01-001", "Tower Bridge", "London", 51.50545, -0.07855, "Europe/London"),
    ("UK-01-002", "Elizabeth Tower", "London", 51.50072, -0.12205, "Europe/London"),
    ("UK-01-003", "Buckingham Palace", "London", 51.50155, -0.14085, "Europe/London"),
    ("UK-01-004", "St Paul's Cathedral", "London", 51.51385, -0.10155, "Europe/London"),
    ("UK-01-005", "Tower of London", "London", 51.50705, -0.07675, "Europe/London"),
    ("UK-01-006", "Trafalgar Square", "London", 51.50745, -0.12805, "Europe/London"),
    ("UK-01-007", "The Shard", "London", 51.50785, -0.08775, "Europe/London"),
    ("UK-01-008", "Royal Observatory", "London", 51.47685, -0.00045, "Europe/London"),
    ("UK-01-009", "British Museum", "London", 51.51855, -0.12655, "Europe/London"),
    ("UK-01-010", "London Eye", "London", 51.50385, -0.11735, "Europe/London"),
    # London afternoon batch, 30 September 2026. England only.
    ("UK-01-011", "Natural History Museum", "London", 51.49605, -0.17640, "Europe/London"),
    ("UK-01-012", "Covent Garden Market", "London", 51.51140, -0.12290, "Europe/London"),
    ("UK-01-013", "Westminster Abbey", "London", 51.49950, -0.12880, "Europe/London"),
    ("UK-01-014", "Tate Modern", "London", 51.50815, -0.09940, "Europe/London"),
    ("UK-01-015", "Kensington Palace", "London", 51.50500, -0.18550, "Europe/London"),
    ("UK-01-016", "Piccadilly Circus", "London", 51.50970, -0.13440, "Europe/London"),
    ("UK-01-017", "Cutty Sark", "London", 51.48335, -0.00950, "Europe/London"),
    ("UK-01-018", "HMS Belfast", "London", 51.50615, -0.08150, "Europe/London"),
    ("UK-01-019", "Southwark Cathedral", "London", 51.50575, -0.08960, "Europe/London"),
    ("UK-01-020", "St Pancras", "London", 51.52870, -0.12550, "Europe/London"),
    ("UK-01-021", "Royal Albert Hall", "London", 51.50042, -0.17728, "Europe/London"),
    ("UK-01-022", "30 St Mary Axe", "London", 51.51412, -0.08105, "Europe/London"),
    ("UK-01-023", "Shakespeare's Globe", "London", 51.50772, -0.09722, "Europe/London"),
    ("UK-01-024", "The Monument", "London", 51.50982, -0.08572, "Europe/London"),
    ("UK-01-025", "Harrods", "London", 51.49905, -0.16365, "Europe/London"),
    ("UK-01-026", "Old Royal Naval College", "London", 51.48445, -0.00935, "Europe/London"),
    ("UK-01-027", "Victoria and Albert Museum", "London", 51.49615, -0.17225, "Europe/London"),
    ("UK-01-028", "Guildhall", "London", 51.51525, -0.09185, "Europe/London"),
    ("UK-01-029", "Lambeth Palace", "London", 51.49555, -0.12015, "Europe/London"),
    ("UK-01-030", "Wellington Arch", "London", 51.50242, -0.15055, "Europe/London"),
    ("UK-01-031", "Battersea Power Station", "London", 51.48355, -0.14470, "Europe/London"),
    ("UK-01-032", "Borough Market", "London", 51.50530, -0.09105, "Europe/London"),
    ("UK-01-033", "Cleopatra's Needle", "London", 51.50855, -0.12020, "Europe/London"),
    ("UK-01-034", "Marble Arch", "London", 51.51330, -0.15890, "Europe/London"),
    ("UK-01-035", "Albert Memorial", "London", 51.50285, -0.17760, "Europe/London"),
    ("UK-01-036", "Banqueting House", "London", 51.50455, -0.12590, "Europe/London"),
    ("UK-01-037", "Leadenhall Market", "London", 51.51270, -0.08345, "Europe/London"),
    ("UK-01-038", "Millennium Bridge", "London", 51.50890, -0.09920, "Europe/London"),
    ("UK-01-039", "Horse Guards", "London", 51.50480, -0.12700, "Europe/London"),
    ("UK-01-040", "Christ Church Spitalfields", "London", 51.51915, -0.07475, "Europe/London"),
    ("UK-01-041", "Somerset House", "London", 51.51080, -0.11715, "Europe/London"),
    ("UK-01-042", "Admiralty Arch", "London", 51.50635, -0.12940, "Europe/London"),
    ("UK-01-043", "Royal Courts of Justice", "London", 51.51305, -0.11320, "Europe/London"),
    ("UK-01-044", "Mansion House", "London", 51.51275, -0.08950, "Europe/London"),
    ("UK-01-045", "Bank of England", "London", 51.51395, -0.08800, "Europe/London"),
    ("UK-01-046", "Golden Hinde II", "London", 51.50675, -0.09035, "Europe/London"),
    ("UK-01-047", "Apsley House", "London", 51.50310, -0.15110, "Europe/London"),
    ("UK-01-048", "Liberty London", "London", 51.51340, -0.14010, "Europe/London"),
    ("UK-01-049", "Selfridges", "London", 51.51420, -0.15260, "Europe/London"),
    ("UK-01-050", "Barbican Centre", "London", 51.51960, -0.09350, "Europe/London"),
    ("UK-01-051", "Hampton Court Palace", "London", 51.40330, -0.33780, "Europe/London"),
    ("UK-01-052", "Kew Gardens Palm House", "London", 51.47890, -0.29550, "Europe/London"),
    ("UK-01-053", "Old Bailey", "London", 51.51555, -0.10195, "Europe/London"),
    ("UK-01-054", "Temple Church", "London", 51.51305, -0.11050, "Europe/London"),
    ("UK-01-055", "Royal Exchange", "London", 51.51340, -0.08760, "Europe/London"),
    ("UK-01-056", "Lloyd's Building", "London", 51.51300, -0.08240, "Europe/London"),
    ("UK-01-057", "One Canada Square", "London", 51.50520, -0.02120, "Europe/London"),
    ("UK-01-058", "City Hall", "London", 51.50475, -0.07845, "Europe/London"),
    ("UK-01-059", "London Stadium", "London", 51.53870, -0.01660, "Europe/London"),
    ("UK-01-060", "Wembley Stadium", "London", 51.55820, -0.27950, "Europe/London"),
    # London night batch, 30 September 2026. England only. Public viewpoints.
    ("UK-01-101", "Kenwood House", "London", 51.57070, -0.16745, "Europe/London"),
    ("UK-01-102", "Syon House", "London", 51.47655, -0.31380, "Europe/London"),
    ("UK-01-103", "Ham House", "London", 51.44435, -0.31415, "Europe/London"),
    ("UK-01-104", "Chiswick House", "London", 51.48335, -0.25870, "Europe/London"),
    ("UK-01-105", "Eltham Palace", "London", 51.44755, 0.04855, "Europe/London"),
    ("UK-01-106", "Royal Opera House", "London", 51.51288, -0.12185, "Europe/London"),
    ("UK-01-107", "Theatre Royal Drury Lane", "London", 51.51305, -0.12055, "Europe/London"),
    ("UK-01-108", "The Roundhouse", "London", 51.54315, -0.15155, "Europe/London"),
    ("UK-01-109", "Camden Lock Market", "London", 51.54125, -0.14485, "Europe/London"),
    ("UK-01-110", "Abbey Road Studios", "London", 51.53185, -0.17815, "Europe/London"),
    # London night batch, 2 October 2026. England only. Public viewpoints.
    # These ten sites are not scenes on main or on Candidate branches through UK-01-320.
    ("UK-01-321", "Blewcoat School", "London", 51.49839, -0.13603, "Europe/London"),
    ("UK-01-322", "Soane Mausoleum", "London", 51.53555, -0.13003, "Europe/London"),
    ("UK-01-323", "Brunel Engine House", "London", 51.50164, -0.05286, "Europe/London"),
    ("UK-01-324", "Vanbrugh Castle", "London", 51.48043, 0.00462, "Europe/London"),
    ("UK-01-325", "Sutton House", "London", 51.54833, -0.05028, "Europe/London"),
    ("UK-01-326", "The Langham", "London", 51.51766, -0.14357, "Europe/London"),
    ("UK-01-327", "Bomber Command Memorial", "London", 51.50333, -0.14889, "Europe/London"),
    ("UK-01-328", "Clock Mill", "London", 51.52720, -0.00720, "Europe/London"),
    ("UK-01-329", "Prospect of Whitby", "London", 51.50720, -0.05100, "Europe/London"),
    ("UK-01-330", "St Etheldreda's Church", "London", 51.51864, -0.10752, "Europe/London"),
]


def existing_stamps() -> set[str]:
    stamps = set()
    if not OUT.exists():
        return stamps
    for path in OUT.glob("UK-*.json"):
        data = json.loads(path.read_text())
        stamps.add(data["retrieval_timestamp"])
    return stamps


def fetch_one(
    entry_id: str,
    site: str,
    city: str,
    lat: float,
    lon: float,
    tz_name: str,
    stamps: set[str],
) -> dict:
    tz = ZoneInfo(tz_name)
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code,cloud_cover,wind_speed_10m,is_day,precipitation",
        "daily": "sunrise,sunset",
        "timezone": tz_name,
        "forecast_days": 1,
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    time.sleep(2.0)
    request_started = datetime.now(tz)
    req = urllib.request.Request(url, headers={"User-Agent": "jasons-vision-united-kingdom/1.0"})
    body = None
    last_err: Exception | None = None
    for _attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                body = resp.read()
            break
        except Exception as err:
            last_err = err
            time.sleep(2.0)
    if body is None:
        raise SystemExit(f"{entry_id} Open-Meteo failed: {last_err}")
    retrieval = datetime.now(tz)
    stamp = retrieval.isoformat(timespec="seconds")
    if stamp in stamps:
        raise SystemExit(f"{entry_id} retrieval second collided: {stamp}")
    payload = json.loads(body)
    current = payload["current"]
    daily = payload["daily"]
    sunrise = daily["sunrise"][0]
    is_day = current["is_day"]
    daynight = "night" if is_day == 0 or stamp[11:16] < sunrise[11:16] else "day"
    record = {
        "entry_id": entry_id,
        "site": site,
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "model_latitude": payload.get("latitude"),
        "model_longitude": payload.get("longitude"),
        "provider": "Open-Meteo",
        "retrieval_timestamp": stamp,
        "retrieval_display": (
            f"{retrieval.day} {MONTHS[retrieval.month]} {retrieval.year} "
            f"{retrieval.strftime('%H:%M:%S')} {tz_name}"
        ),
        "request_started": request_started.isoformat(timespec="seconds"),
        "model_time": current["time"],
        "model_interval_seconds": current.get("interval", 900),
        "timezone": payload.get("timezone", tz_name),
        "temperature_2m": current["temperature_2m"],
        "weather_code": current["weather_code"],
        "cloud_cover": current["cloud_cover"],
        "wind_speed_10m": current["wind_speed_10m"],
        "is_day": is_day,
        "precipitation": current["precipitation"],
        "sunrise": sunrise,
        "sunset": daily["sunset"][0],
        "model_valid_hour_start": retrieval.strftime("%Y-%m-%dT%H:00"),
        "scenario_label": (
            f"{retrieval.day} {MONTHS[retrieval.month]} {retrieval.year} · "
            f"{retrieval.strftime('%H:%M')} {tz_name}"
        ),
        "daynight": daynight,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{entry_id}.json").write_text(json.dumps(record, indent=2) + "\n")
    stamps.add(stamp)
    print(entry_id, stamp, "daynight", daynight, "code", record["weather_code"])
    return record


def main() -> None:
    stamps = existing_stamps()
    for row in SCENES:
        if (OUT / f"{row[0]}.json").exists():
            print(f"keep {row[0]}")
            continue
        fetch_one(*row, stamps)


if __name__ == "__main__":
    main()
