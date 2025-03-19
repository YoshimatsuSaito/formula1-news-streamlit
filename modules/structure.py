from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class SiteStructure:
    prefix_home: str
    news_home: str
    scrape_title: str
    get_title: Callable
    scrape_link: str
    get_link: Callable


@dataclass(frozen=True)
class ResultStructure:
    name: str
    list_title: list[str]
    list_link: list[str]

    @property
    def dict_title_link(self) -> dict[str, str]:
        return {k: v for k, v in zip(self.list_title, self.list_link)}

    def is_empty(self) -> bool:
        if len(self.list_title) == 0 or len(self.list_link) == 0:
            return True
        else:
            return False
