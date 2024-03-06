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
    df_season_calendar = get_this_season_calendar()
    list_event_name = ["fp1", "fp2", "fp3", "qualifying", "sprint", "race"]

    df_latest_gp = df_season_calendar.loc[
        df_season_calendar["is_latest_gp"] == 1
    ].reset_index(drop=True)
    st.header(f"Next: {df_latest_gp.at[0, 'gp_round_name']}")
    cols = st.columns(len(list_event_name))
    for idx, event_name in enumerate(list_event_name):
        with cols[idx]:
            st.caption(event_name)
            event_time = df_latest_gp.at[0, event_name]
            event_time = (
                event_time.strftime("%m/%d %a %H:%M")
                if isinstance(event_time, pd.Timestamp)
                else "TBA/Not held"
            )
            st.info(event_time)

    with st.expander("Season calendar"):
        for idx, row in df_season_calendar.iterrows():
            st.header(row.gp_round_name)
            list_event_name = ["fp1", "fp2", "fp3", "qualifying", "sprint", "race"]
            cols = st.columns(len(list_event_name))
            for idx, event_name in enumerate(list_event_name):
                with cols[idx]:
                    st.caption(event_name)
                    event_time = row[event_name]
                    event_time = (
                        event_time.strftime("%m/%d %a %H:%M")
                        if isinstance(event_time, pd.Timestamp)
                        else "TBA/Not held"
                    )
                    st.info(event_time)
                    st.markdown("---")
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
