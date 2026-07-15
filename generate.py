import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from jinja2 import Environment, FileSystemLoader, select_autoescape

from modules.load_config import load_config
from modules.schedule import fetch_season_schedule
from modules.scraper import scrape_news
from modules.structure import ResultStructure
from modules.trends import analyze_trends

JST = timezone(timedelta(hours=9))


def main() -> None:
    config = load_config(Path("./config/config.yaml"))

    sources = []
    for name, site_structure in config.items():
        try:
            result = scrape_news(name=name, site_structure=site_structure)
            if not result.is_empty():
                sources.append(_to_template_source(result, site_structure.news_home))
                print(f"[OK] {name}: {len(result.list_title)} items")
            else:
                print(f"[SKIP] {name}: 0 items")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    year = datetime.now(JST).year
    schedule = []
    try:
        schedule = fetch_season_schedule(year)
        print(f"[OK] schedule: {len(schedule)} rounds (year={year})")
    except Exception as e:
        print(f"[WARN] schedule: {e}")

    trends = {}
    try:
        trends = analyze_trends(sources)
        print(
            f"[OK] trends: {trends['total_articles']} titles analyzed "
            f"({len(trends['drivers'])} drivers, {len(trends['teams'])} teams, "
            f"{len(trends['topics'])} topics, {len(trends['keywords'])} keywords)"
        )
    except Exception as e:
        print(f"[WARN] trends: {e}")

    updated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    html = _render(sources, schedule, trends, year, updated_at)
    Path("index.html").write_text(html, encoding="utf-8")
    print(f"\nGenerated index.html ({len(sources)} sources, {updated_at})")


def _to_template_source(result: ResultStructure, url: str) -> dict:
    key = result.name.lower().replace(" ", "-").replace("/", "-")
    return {
        "key":      key,
        "name":     result.name,
        "url":      url,
        "articles": [
            {"title": t, "link": l}
            for t, l in zip(result.list_title, result.list_link)
            if t and l
        ],
    }


def _render(
    sources: list[dict],
    schedule: list[dict],
    trends: dict,
    year: int,
    updated_at: str,
) -> str:
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html.j2")
    return template.render(
        sources=sources,
        source_keys_json=json.dumps([s["key"] for s in sources]),
        schedule=schedule,
        trends=trends,
        current_year=year,
        updated_at=updated_at,
    )


if __name__ == "__main__":
    main()
