import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

from jinja2 import Environment, FileSystemLoader, select_autoescape

from modules.load_config import load_config
from modules.scraper import scrape_news
from modules.structure import ResultStructure

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

    updated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    html = _render(sources, updated_at)
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


def _render(sources: list[dict], updated_at: str) -> str:
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("index.html.j2")
    return template.render(
        sources=sources,
        source_keys_json=json.dumps([s["key"] for s in sources]),
        updated_at=updated_at,
    )


if __name__ == "__main__":
    main()
