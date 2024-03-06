import pandas as pd
import streamlit as st

from modules.race_calendar import get_this_season_calendar
from modules.scraper import NewsScraper


@st.cache_resource(ttl=60 * 5, show_spinner=False)
def get_news(_ns):
    """
    5分間はscrapingの状態をキャッシュする
    ニュースを見るというアクション単位では都度scrapingをしてほしいが、
    一回のアクションの最中にブラウザの切り替えなどをした際にいちいちやり直される必要はない
    """
    _ns.get_news_info()
    return _ns


def main():
    st.title("Formula 1")
    st.markdown("---")

    # カレンダー表示
    df_season_calendar = get_this_season_calendar()
    list_event_name = ["fp1", "fp2", "fp3", "qualifying", "sprint", "race"]
    latest_idx = df_season_calendar.loc[df_season_calendar["is_latest_gp"] == 1].index[
        0
    ]
    df_target = df_season_calendar[["gp_name"] + list_event_name]
    for event_name in list_event_name:
        df_target[event_name] = df_target[event_name].apply(
            lambda x: (
                x.strftime("%m/%d %a %H:%M")
                if isinstance(x, pd.Timestamp)
                else "TBA/Not held"
            )
        )
    st.dataframe(
        df_target.style.applymap(
            lambda _: "background-color: CornflowerBlue;",
            subset=(
                [latest_idx],
                slice(None),
            ),
        ),
        height=200,
        hide_index=True,
    )
    st.markdown("---")

    st.header("Today and yesterday's news")
    ns = NewsScraper()
    with st.spinner("Now scraping..."):
        # 5分間のキャッシュ情報
        ns = get_news(ns)
        if len(ns.df_today_news["site_name"]) > 0:
            for site_name in ns.df_today_news["site_name"].unique():
                df_target = ns.df_today_news[
                    ns.df_today_news["site_name"] == site_name
                ].reset_index(drop=True)
                st.subheader(site_name)
                for idx in range(len(df_target)):
                    news_link = df_target.iloc[idx]["news_link"]
                    news_title = df_target.iloc[idx]["news_title"]
                    st.markdown(
                        f"<a href='{news_link}' target='_blank' rel='noopener noreferrer'>{news_title}</a>",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown("Nothing so far")

    st.markdown("---")
    with st.expander("Target to scrape"):
        for site_name in ns.dict_site_structure.keys():
            site_home = ns.dict_site_structure[site_name]["url"]
            st.markdown(
                f"<a href='{site_home}' target='_blank' rel='noopener noreferrer'>{site_name}</a>",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
