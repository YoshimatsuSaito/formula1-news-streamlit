import streamlit as st

from modules.news_scraper import NewsScraper

def main():
    st.title("Formula 1")
    st.header("Today's News")
    ns = NewsScraper()
    with st.expander("Target to scrape"):
        for site_name in ns.dict_site_structure.keys():
            site_home = ns.dict_site_structure[site_name]["url"]
            st.markdown(
                f"<a href='{site_home}' style='color:white' target='_blank' rel='noopener noreferrer'>{site_name}</a>",
                unsafe_allow_html=True
            )
    with st.spinner('Now scraping...'):
        ns.get_news_info()
        for site_name in ns.df_today_news["site_name"].unique():
            df_target = ns.df_today_news[ns.df_today_news["site_name"]==site_name].reset_index(drop=True)
            st.subheader(site_name)
            for idx in range(len(df_target)):
                news_link = df_target.iloc[idx]["news_link"]
                news_title = df_target.iloc[idx]["news_title"]
                st.markdown(
                    f"<a href='{news_link}' style='color:white' target='_blank' rel='noopener noreferrer'>{news_title}</a>", unsafe_allow_html=True,
                )

if __name__ == "__main__":
    main()