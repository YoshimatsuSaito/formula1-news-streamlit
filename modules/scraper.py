import datetime as dt
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pytz import timezone

import pandas as pd
import requests
from bs4 import BeautifulSoup as bs


def get_nextgp_schedule():
    """
    次のグランプリの日程を取得して返す便利用関数
    """
    url = "https://formula1-data.com/race/gp"
    r = requests.get(url)
    soup = bs(r.text, "lxml")
    list_event_name = [x.contents[0] for x in soup.select(".nextGp__result h3")]
    list_event_time = [x.contents[0] for x in soup.select(".nextGp__result time")]
    gp_name = soup.select(".nextGp__title")[0].contents[2]
    return list_event_name, list_event_time, gp_name

class NewsScraper():
    """
    スクレイピングを行うクラス
    上記のCommandクラス内で用いる
    """
    def __init__(self, page_nums=8):
        # 比較演算子を使用するために以下のように定義する
        now = datetime.now(timezone("Asia/Tokyo"))
        self.today = dt.datetime(now.year, now.month, now.day, 0, 0, 0)
        # 何日前までさかのぼるか指定
        gb = timedelta(days=1)
        self.gb_day = self.today - gb
        # 収集するページ数
        self.page_nums = page_nums
        # 各ニュースサイトのスクレイピングに必要な情報（htmlを人力で見た結果）
        self.dict_site_structure = {
            "F1-Gate.com": 
                {"url":"https://f1-gate.com", "page_format":"/page_", "tail_format":".html", 
                    "scrape_title":".content h2 a", "get_title":lambda x: x.contents[0], 
                    "scrape_link":".content h2 a", "get_link":lambda x: x.attrs['href'], 
                    "scrape_date":".content>.contentitem", "get_date":lambda x: x.contents[0],
                    "strptime_format":"%Y年%m月%d日", "link_head":"",
                    "page_start":1, "page_add":1},
            "BELLAGARA": 
                {"url":"https://bellagara.com/news", "page_format":"/page/", "tail_format":"", 
                    "scrape_title":".uk-card-title", "get_title":lambda x: x.contents[0].contents[0], 
                    "scrape_link":".uk-card-title", "get_link":lambda x: x.contents[0].attrs['href'], 
                    "scrape_date":".uk-width-expand>.uk-card-body>.uk-text-meta.uk-margin-small>time", "get_date":lambda x: x.contents[0][:10],
                    "strptime_format":"%Y.%m.%d", "link_head":"",
                    "page_start":1, "page_add":1},
            "motorsport.com":
                {"url":"https://jp.motorsport.com/f1/news/", "page_format":"?p=", "tail_format":"", 
                    "scrape_title":".ms-content_main .ms-item_title>.ms-item_link--text", "get_title":lambda x: x.attrs['title'], 
                    "scrape_link":".ms-content_main .ms-item_title>.ms-item_link--text", "get_link":lambda x: x.attrs['href'], 
                    "scrape_date":".ms-content_main .ms-item_info-top>.ms-item_date .ms-item_date-value", "get_date":lambda x: x.attrs['datetime'][:10],
                    "strptime_format":"%Y-%m-%d", "link_head":"https://jp.motorsport.com",
                    "page_start":1, "page_add":1},
            "F1情報通":
                {"url":"http://f1jouhou2.blog.fc2.com", "page_format":"/page-", "tail_format":".html", 
                    "scrape_title":"body #all .separate .index_title .index_h2 a", "get_title":lambda x: x.contents[0], 
                    "scrape_link":"body #all .separate .index_title .index_h2 a", "get_link":lambda x: x.attrs['href'], 
                    "scrape_date":"body #all .separate .title_date", "get_date":lambda x: x.contents[0][-10:], 
                    "strptime_format":"%Y-%m-%d", "link_head":"",
                    "page_start":0, "page_add":1},
            "autosport-japan":
                {"url":"https://www.as-web.jp/f1/news", "page_format":"/", "tail_format":"", 
                    "scrape_title":"#topF1News .listTitle a", "get_title":lambda x: x.contents[0], 
                    "scrape_link":"#topF1News .listTitle a", "get_link":lambda x: x.attrs['href'], 
                    "scrape_date":"#topF1News .margin_0.h5 span", "get_date":lambda x: x.contents[0], 
                    "strptime_format":"%Y/%m/%d", "link_head":"https://www.as-web.jp",
                    "page_start":1, "page_add":1},
            "BBC":
                {"url":"https://www.bbc.com/sport/formula1", "page_format":"", "tail_format":"", 
                    "scrape_title":(".gs-c-promo-heading__title.gel-double-pica-bold.sp-o-link-split__text,"
                                    ".gs-c-promo-heading__title.gel-pica-bold.sp-o-link-split__text"), "get_title":lambda x: x.contents[0], 
                    "scrape_link":(".gs-c-promo-heading.gs-o-faux-block-link__overlay-link.sp-o-link-split__anchor.gel-double-pica-bold,"
                                ".gs-c-promo-heading.gs-o-faux-block-link__overlay-link.sp-o-link-split__anchor.gel-pica-bold"), "get_link":lambda x: x.attrs['href'], 
                    "scrape_date":".gs-o-bullet__text.qa-status-date.gs-u-align-middle.gs-u-display-inline", "get_date":lambda x: x.attrs['datetime'][:10],
                    "strptime_format":"%Y-%m-%d", "link_head":"https://www.bbc.com",
                    "page_start":-1000, "page_add":""},
            "autosport":
                {"url":"https://www.autosport.com/f1/news/", "page_format":"?p=", "tail_format":"", 
                    "scrape_title":".ms-grid-hor-items-1-2-3-4-5 .ms-item_link.ms-item_link--text", "get_title":lambda x: x['title'], 
                    "scrape_link":".ms-grid-hor-items-1-2-3-4-5 .ms-item_link.ms-item_link--text", "get_link":lambda x: x['href'], 
                    "scrape_date":".ms-grid-hor-items-1-2-3-4-5 .ms-item_date-value", "get_date":lambda x: x['datetime'][:10], 
                    "strptime_format":"%Y-%m-%d", "link_head":"https://www.autosport.com",
                    "page_start":1, "page_add":1},
            "skysports":
                {"url":"https://www.skysports.com/f1/news", "page_format":"/more/", "tail_format":"", 
                    "scrape_title":".news-list.block .news-list__headline a", "get_title":lambda x: x.contents[0], 
                    "scrape_link":".news-list.block .news-list__headline a", "get_link":lambda x: x.attrs['href'], 
                    "scrape_date":".news-list.block .label__timestamp", "get_date":lambda x: x.contents[0][:8], 
                    "strptime_format":"%d/%m/%y", "link_head":"",
                    "page_start":1, "page_add":1}
        }
        # 結果格納用のリスト変数
        self.list_site_name = list()
        self.list_news_title = list()
        self.list_news_link = list()
        self.list_ymd = list()
        self.list_site_name_today = list()
        self.list_news_title_today = list()
        self.list_news_link_today = list()
        self.list_ymd_today = list()

    def scrape_news(self, site_name):
        """
        サイトの情報を抜き出す関数
        page_numsページ数を上限まで確認、もしくは、gb_day以前のデータが得られる、のいずれかが満たされたらスクレイピングを終える
        """
        site_info = self.dict_site_structure[site_name]
        url = site_info["url"]
        page_format = site_info["page_format"]
        tail_format = site_info["tail_format"]
        scrape_title = site_info["scrape_title"]
        get_title = site_info["get_title"]
        scrape_link = site_info["scrape_link"]
        get_link = site_info["get_link"]
        scrape_date = site_info["scrape_date"]
        get_date = site_info["get_date"]
        strptime_format = site_info["strptime_format"]
        link_head = site_info["link_head"]
        page = site_info["page_start"]
        page_add = site_info["page_add"]
        titles, links, ymds = [], [], []
        # 取得したページの日付情報の初期値は本日の日付とする
        page_day = self.today
        while (page_day >= self.gb_day) and (page <= self.page_nums):
            if page == -1000: page = ""
            headers_dic = {"User-Agent": "hoge"}
            r = requests.get(f"{url}{page_format}{page}{tail_format}", headers=headers_dic)
            soup = bs(r.text, "lxml")
            titles += [get_title(x) for x in soup.select(scrape_title)] # 記事タイトル
            links += [f"{link_head}{get_link(x)}" for x in soup.select(scrape_link)]# 記事リンク
            ymds += [datetime.strptime(get_date(x), strptime_format) for x in soup.select(scrape_date)] # 日付(一つの記事に複数の日付はつかないことを前提とする)
            # 取得したページの日付で更新する
            page_day = ymds[-1]
            if page!="":
                page += page_add
            else:
                break
        self.list_site_name += [site_name]*len(ymds)
        self.list_news_title += titles[:len(ymds)]
        self.list_news_link += links[:len(ymds)]
        self.list_ymd += ymds

    def scrape_news_and_extract_today(self):
        """
        サイト情報をスクレイピングして整形
        """
        for site_name in list(self.dict_site_structure.keys()):
            try:
                # ニュースをスクレイピング（複数日付が混じっている）
                self.scrape_news(site_name)
            except:
                pass
        # 今日の日付のニュースのみを取り出す
        for site_name, news_title, news_link, ymd in zip(
            self.list_site_name, 
            self.list_news_title,
            self.list_news_link, 
            self.list_ymd
        ):
            if ymd >= self.gb_day:
                self.list_site_name_today.append(site_name)
                self.list_news_title_today.append(news_title)
                self.list_news_link_today.append(news_link)
                self.list_ymd_today.append(ymd)

    def get_news_info(self):
        """
        全体のメイン関数的な役割
        """
        # ニュースのスクレイピング
        self.scrape_news_and_extract_today()
        self.df_today_news = pd.DataFrame({"site_name":self.list_site_name_today, "news_title":self.list_news_title_today, "news_link":self.list_news_link_today})
