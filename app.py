from pathlib import Path

import streamlit as st

from modules.load_config import load_config
from modules.structure import SiteStructure, ResultStructure
from modules.scraper import scrape_news

DICT_SITE_STRUCTURE = load_config(Path("./config/config.yaml"))


st.title("Formula 1 Latest News")

with st.spinner("Now scraping..."):
    for name, site_structure in DICT_SITE_STRUCTURE.items():
        result_structure = scrape_news(name=name, site_structure=site_structure)
        if result_structure.is_empty():
            continue
        st.subheader(name)
        for title, link in zip(result_structure.list_title, result_structure.list_link):
            st.markdown(
                f"<a href='{link}' target='_blank' rel='noopener noreferrer'>{title}</a>",
                unsafe_allow_html=True,
            )

st.markdown("---")
with st.expander("Target to scrape"):
    for name, site_structure in DICT_SITE_STRUCTURE.items():
        st.markdown(
            f"<a href='{site_structure.news_home}' target='_blank' rel='noopener noreferrer'>{name}</a>",
            unsafe_allow_html=True,
        )
