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
    # London evening batch, 30 September 2026. England only.
    # Pins are the public viewpoint, not a surveyed tripod mark.
    # UK-01-096 is the Cabot Square fountain alone, not One Canada Square.
    # UK-01-099 is the Temperate House alone, not the Palm House.
    ("UK-01-091", "Spencer House", "London", 51.50522, -0.14095, "Europe/London"),
    ("UK-01-092", "Middle Temple Hall", "London", 51.51312, -0.11148, "Europe/London"),
    ("UK-01-093", "Charterhouse", "London", 51.52070, -0.09985, "Europe/London"),
    ("UK-01-094", "Museum of London Docklands", "London", 51.50715, -0.02355, "Europe/London"),
    ("UK-01-095", "Greenwich Market", "London", 51.48162, -0.00900, "Europe/London"),
    ("UK-01-096", "Cabot Square", "London", 51.50525, -0.02285, "Europe/London"),
    ("UK-01-097", "Tottenham Hotspur Stadium", "London", 51.60315, -0.06625, "Europe/London"),
    ("UK-01-098", "Twickenham Stadium", "London", 51.45615, -0.33980, "Europe/London"),
    ("UK-01-099", "Kew Gardens Temperate House", "London", 51.47815, -0.29520, "Europe/London"),
    ("UK-01-100", "Osterley Park House", "London", 51.48820, -0.34870, "Europe/London"),
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
