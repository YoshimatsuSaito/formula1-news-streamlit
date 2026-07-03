from pathlib import Path
from datetime import datetime, timezone, timedelta
from html import escape

from modules.load_config import load_config
from modules.scraper import scrape_news
from modules.structure import ResultStructure

JST = timezone(timedelta(hours=9))


def main() -> None:
    config = load_config(Path("./config/config.yaml"))

    results: list[tuple[ResultStructure, str]] = []
    for name, site_structure in config.items():
        try:
            result = scrape_news(name=name, site_structure=site_structure)
            if not result.is_empty():
                results.append((result, site_structure.news_home))
                print(f"[OK] {name}: {len(result.list_title)} items")
            else:
                print(f"[SKIP] {name}: 0 items")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    updated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")
    html = _build_html(results, updated_at)
    Path("index.html").write_text(html, encoding="utf-8")
    print(f"\nGenerated index.html ({len(results)} sources, {updated_at})")



def _build_html(results: list[tuple[ResultStructure, str]], updated_at: str) -> str:
    sections = "\n".join(_build_section(r, url) for r, url in results)

    return f"""\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Formula 1 Latest News</title>
  <style>
    :root {{
      --f1-red: #E10600;
      --bg: #111;
      --card-bg: #1c1c1c;
      --text: #f0f0f0;
      --text-muted: #888;
      --border: #2a2a2a;
      --hover-bg: #272727;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.5;
      min-height: 100vh;
    }}
    header {{
      background: var(--f1-red);
      padding: 20px 32px;
      display: flex;
      align-items: baseline;
      gap: 16px;
      flex-wrap: wrap;
    }}
    header h1 {{
      font-size: 1.6rem;
      font-weight: 800;
      color: #fff;
      letter-spacing: -0.3px;
      white-space: nowrap;
    }}
    header .updated {{
      color: rgba(255,255,255,0.7);
      font-size: 0.8rem;
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 28px 20px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: var(--card-bg);
      border-radius: 10px;
      border: 1px solid var(--border);
      overflow: hidden;
    }}
    .card-header {{
      padding: 12px 16px;
      border-bottom: 2px solid var(--f1-red);
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .card-header a {{
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--f1-red);
      text-decoration: none;
      text-transform: uppercase;
      letter-spacing: 0.6px;
    }}
    .card-header a:hover {{ text-decoration: underline; }}
    .news-list {{ list-style: none; padding: 8px 0; }}
    .news-item a {{
      display: block;
      padding: 7px 16px;
      color: var(--text);
      text-decoration: none;
      font-size: 0.86rem;
      border-left: 3px solid transparent;
      transition: border-color 0.12s, background 0.12s;
    }}
    .news-item a:hover {{
      border-left-color: var(--f1-red);
      background: var(--hover-bg);
    }}
    footer {{
      text-align: center;
      padding: 20px;
      color: var(--text-muted);
      font-size: 0.76rem;
      border-top: 1px solid var(--border);
      margin-top: 8px;
    }}
    @media (max-width: 640px) {{
      main {{ grid-template-columns: 1fr; padding: 16px 12px; }}
      header {{ padding: 16px 20px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>&#x1F3CE;&#xFE0F; Formula 1 Latest News</h1>
    <span class="updated">Last updated: {escape(updated_at)}</span>
  </header>
  <main>
    {sections}
  </main>
  <footer>Auto-updated every 30 minutes &middot; Powered by GitHub Actions + Amazon S3</footer>
</body>
</html>"""


def _build_section(result: ResultStructure, site_url: str) -> str:
    items = "\n".join(
        f'      <li class="news-item">'
        f'<a href="{escape(link)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a>'
        f"</li>"
        for title, link in zip(result.list_title, result.list_link)
        if title and link
    )
    return f"""\
    <div class="card">
      <div class="card-header">
        <a href="{escape(site_url)}" target="_blank" rel="noopener noreferrer">{escape(result.name)}</a>
      </div>
      <ul class="news-list">
{items}
      </ul>
    </div>"""


if __name__ == "__main__":
    main()
