"""Scrape the public GitHub contribution calendar into data/contributions.json.

GitHub serves every user's contribution calendar as plain HTML at
https://github.com/users/<username>/contributions — no token, no API quota.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = (
    os.environ.get("GH_USER")
    or os.environ.get("GITHUB_REPOSITORY_OWNER")
    or "AKCodez"
)
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch_html() -> str:
    headers = {"User-Agent": "Mozilla/5.0 (profile-art; +https://github.com/AKCodez/AKCodez)"}
    last_err = None
    for attempt in range(4):
        try:
            r = requests.get(URL, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.text
            last_err = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last_err = str(e)
        time.sleep(2 * (attempt + 1))
    sys.exit(f"failed to fetch {URL}: {last_err}")


def parse(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Per-day counts live in <tool-tip for="contribution-day-component-R-C"> siblings.
    counts = {}
    for tip in soup.select('tool-tip[for^="contribution-day-component"]'):
        text = tip.get_text(strip=True)
        m = re.match(r"(No|[\d,]+)\s+contributions?", text)
        if not m:
            continue
        raw = m.group(1)
        counts[tip["for"]] = 0 if raw == "No" else int(raw.replace(",", ""))

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        cid = td.get("id", "")
        m = re.match(r"contribution-day-component-(\d+)-(\d+)", cid)
        weekday, week = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        days.append(
            {
                "date": td["data-date"],
                "level": int(td.get("data-level", 0)),
                "count": counts.get(cid, 0),
                "week": week,
                "weekday": weekday,
            }
        )
    days.sort(key=lambda d: d["date"])

    total = sum(d["count"] for d in days)
    h2 = soup.select_one("#js-contribution-activity-description")
    if h2:
        m = re.search(r"([\d,]+)\s+contributions", h2.get_text(" ", strip=True))
        if m:
            total = int(m.group(1).replace(",", ""))

    return {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total": total,
        "days": days,
    }


def main() -> None:
    data = parse(fetch_html())
    if len(data["days"]) < 300:
        sys.exit(f"parsed only {len(data['days'])} day cells — GitHub markup may have changed")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{data['total']} contributions across {len(data['days'])} days -> {OUT.name}")


if __name__ == "__main__":
    main()
