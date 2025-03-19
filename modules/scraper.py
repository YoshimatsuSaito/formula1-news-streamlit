import requests
from bs4 import BeautifulSoup as bs

from .structure import SiteStructure, ResultStructure


def scrape_news(
    name: str, site_structure: SiteStructure, max_num: int = 10
) -> ResultStructure:
    """
    サイトの情報を抜き出す関数
    """
    headers_dic = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(site_structure.news_home, headers=headers_dic)
    soup = bs(r.text, "lxml")
    list_title = [
        site_structure.get_title(x) for x in soup.select(site_structure.scrape_title)
    ]
    list_link = [
        f"{site_structure.prefix_home}{site_structure.get_link(x)}"
        for x in soup.select(site_structure.scrape_link)
    ]

    return ResultStructure(
        name=name, list_link=list_link[:max_num], list_title=list_title[:max_num]
    )
