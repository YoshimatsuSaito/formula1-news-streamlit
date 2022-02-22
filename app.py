import streamlit as st
from bs4 import BeautifulSoup as bs

from modules.news_scraper import NewsScraper

def main():
    st.title("Formula 1")
    st.header("Today's News")
    with st.spinner('Now scraping...'):
        ns = NewsScraper()
        ns.get_news_info()
        for site_name in ns.df_today_news["site_name"].unique():
            df_target = ns.df_today_news[ns.df_today_news["site_name"]==site_name].reset_index(drop=True)
            st.subheader(site_name)
            for idx in range(len(df_target)):
                news_link = df_target.iloc[idx]["news_link"]
                news_title = df_target.iloc[idx]["news_title"]
                st.markdown(
                    f"<a href='{news_link}' target='_blank' rel='noopener noreferrer'>{news_title}</a>", unsafe_allow_html=True,
                )

if __name__ == "__main__":
    main()