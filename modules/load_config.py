from pathlib import Path

import yaml

from .structure import SiteStructure


def load_config(config_path: Path) -> dict[str, SiteStructure]:
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    dict_site_structure = dict()
    for site in config["sites"]:
        site_info = config["sites"][site]
        dict_site_structure[site] = SiteStructure(
            prefix_home=site_info["prefix_home"],
            news_home=site_info["news_home"],
            scrape_title=site_info["scrape_title"],
            scrape_link=site_info["scrape_link"],
            get_title=eval(site_info["get_title"]),
            get_link=eval(site_info["get_link"]),
        )
    return dict_site_structure
