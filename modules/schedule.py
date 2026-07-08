from datetime import datetime, timezone, timedelta
from typing import Optional

import requests

_API_BASE = "https://api.jolpi.ca/ergast/f1"
_UTC = timezone.utc
JST = timezone(timedelta(hours=9))

# Ordered list of session field names → display labels.
# SprintQualifying (2023) and SprintShootout (2024+) map to the same label;
# whichever appears first in a given race dict wins.
_SESSION_FIELDS = [
    ("FirstPractice",    "FP1"),
    ("SecondPractice",   "FP2"),
    ("SprintQualifying", "Sprint Qualifying"),
    ("SprintShootout",   "Sprint Qualifying"),
    ("ThirdPractice",    "FP3"),
    ("Sprint",           "Sprint"),
    ("Qualifying",       "Qualifying"),
    ("race",             "Race"),
]


def fetch_season_schedule(year: int) -> list[dict]:
    url = f"{_API_BASE}/{year}.json?limit=30"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    races = r.json()["MRData"]["RaceTable"]["Races"]

    rounds = []
    next_set = False

    for race in races:
        sessions = _parse_sessions(race)
        race_session = next((s for s in sessions if s["label"] == "Race"), None)
        is_past = race_session["is_past"] if race_session else True

        is_next = False
        if not is_past and not next_set:
            is_next = True
            next_set = True

        rounds.append({
            "round":   int(race["round"]),
            "name":    race["raceName"],
            "circuit": race["Circuit"]["circuitName"],
            "country": race["Circuit"]["Location"]["country"],
            "sessions": sessions,
            "is_past": is_past,
            "is_next": is_next,
        })

    return rounds


def _parse_sessions(race: dict) -> list[dict]:
    now_utc = datetime.now(_UTC)
    sessions = []
    seen_labels: set[str] = set()

    for key, label in _SESSION_FIELDS:
        if label in seen_labels:
            continue
        if key == "race":
            date = race.get("date")
            time = race.get("time")
        else:
            s = race.get(key)
            if s is None:
                continue
            date = s.get("date")
            time = s.get("time")

        dt_jst, is_past = _parse_dt(date, time, now_utc)
        sessions.append({"label": label, "dt_jst": dt_jst, "is_past": is_past})
        seen_labels.add(label)

    return sessions


def _parse_dt(
    date: Optional[str], time: Optional[str], now_utc: datetime
) -> tuple[str, bool]:
    if not date:
        return "", False
    try:
        if time:
            dt_utc = datetime.fromisoformat(
                f"{date}T{time.rstrip('Z')}"
            ).replace(tzinfo=_UTC)
        else:
            dt_utc = datetime.fromisoformat(date).replace(tzinfo=_UTC)

        dt_jst = dt_utc.astimezone(JST)
        is_past = dt_utc < now_utc
        return dt_jst.strftime("%-m/%-d %H:%M"), is_past
    except (ValueError, OSError):
        return date, False
