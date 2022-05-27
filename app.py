import streamlit as st

from modules.scraper import NewsScraper, get_nextgp_schedule

def main():
    st.title("Formula 1")
    st.markdown("---")
    list_event_name, list_event_time, gp_name = get_nextgp_schedule()
    st.header(f"Next Grand Prix ({gp_name}) Schedule")
    cols = st.columns(len(list_event_name))
    for idx, event_name, event_time in zip(range(len(cols)), list_event_name, list_event_time):
        with cols[idx]:
            st.caption(event_name)
            st.info(event_time)
    st.markdown("---")
    st.header("Today and yesterday's news")
    ns = NewsScraper()
    with st.expander("Target to scrape"):
        for site_name in ns.dict_site_structure.keys():
            site_home = ns.dict_site_structure[site_name]["url"]
            st.markdown(
                f"<a href='{site_home}' target='_blank' rel='noopener noreferrer'>{site_name}</a>",
                unsafe_allow_html=True
            )
    with st.spinner('Now scraping...'):
        ns.get_news_info()
        if len(ns.df_today_news["site_name"]) > 0:
            for site_name in ns.df_today_news["site_name"].unique():
                df_target = ns.df_today_news[ns.df_today_news["site_name"]==site_name].reset_index(drop=True)
                st.subheader(site_name)
                for idx in range(len(df_target)):
                    news_link = df_target.iloc[idx]["news_link"]
                    news_title = df_target.iloc[idx]["news_title"]
                    st.markdown(
                        f"<a href='{news_link}' target='_blank' rel='noopener noreferrer'>{news_title}</a>", unsafe_allow_html=True,
                    )
        else:
            st.markdown("Nothing so far")

if __name__ == "__main__":
    main()