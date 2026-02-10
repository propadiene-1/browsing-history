import streamlit as st
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pathlib import Path

st.set_page_config(page_title = "Understand your Recent Search Behavior", layout="wide")

# ------------------------
# VISUALIZE SEARCH RESULTS
# ------------------------

#make wordcloud from queries df
def render_wordcloud(raw_data):
    raw_data = raw_data.sort_values(by='visit_time').reset_index(drop=True)
    query_indices = raw_data[raw_data['title'].str.contains('Google Search', na=False)].index #mask with google search

    if len(query_indices) == 0:
        st.info("No google searches were found in your history.")
        return
    
    st.markdown("### Most Common Search Words")
    st.markdown("This word cloud aggregates all the words from your search queries (anything you type into your search bar).")
    #wordlist = []

    google_searches = raw_data[
        raw_data['title'].str.contains('Google Search', na=False, case=False)
    ].copy()

    if google_searches.empty:
        st.info("No searches were found in your history.")
        return
    
    #replace all Google Search ending
    google_searches['query'] = google_searches['title'].str.replace('- Google Search', '', regex=False)
    all_words = ' '.join(google_searches['query'].dropna().astype(str))
    
    if not all_words.strip():
        st.info("No valid words in search queries")
        return

    with st.spinner('Generating word cloud...'):
        wordcloud = WordCloud(
            width=1000,
            height=500,
            background_color='white',
            colormap='Blues_r',  # Example: use a specific color map
            max_words=200,
            font_path = Path(__file__).parent / "Source_Sans_3" / "SourceSans3-Regular.ttf",
            #"/Users/propadiene/cloned-repos/browsing-history-app/pages/Source_Sans_3/SourceSans3-Regular.ttf",
            scale=2, # Increase scale for higher resolution on save
            random_state=16     #set random state for reproducible results
        ).generate(all_words)

    if wordcloud is None:
        st.info("Could not generate word cloud")
        return

    #display wordcloud
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)
    plt.close(fig)

    return

#shows 10 searches after a query
def render_query_table(raw_data, limit=30):
    raw_data = raw_data.sort_values(by='visit_time').reset_index(drop=True)
    query_indices = raw_data[raw_data['title'].str.contains('Google Search', na=False)].index #mask with google search

    if len(query_indices) == 0:
        st.info("No google searches were found in your history.")
        return
    st.markdown("### Recent Search Behavior")
    st.markdown(f"Below you can view {min(limit, len(query_indices))} of your most recent searches. Each one opens a dropdown, revealing the next 10 sites that you visited after entering the search.")

    #only go up to the last [limit] searches
    recent_searches = query_indices[::-1][:limit]

    for search_index in recent_searches:
        row = raw_data.iloc[search_index] #look up query in full data table
        if pd.isna(row['title']) or not isinstance(row['title'], str):
            search_title = "Untitled Search"
        else:
            search_title = row['title'].replace('- Google Search', '')
        search_results = raw_data.iloc[search_index+1 : search_index+11][['visit_time', 'domain', 'url', 'title']]
        if search_index + 1 >= len(raw_data):
            st.info("No results after this search")
            continue
        
        with st.expander(f"{search_title} | {row['visit_time']}"): #display in streamlit
            st.dataframe(search_results, hide_index=True, width='stretch')
    return query_indices    #return the df of queries

st.markdown("## Explore your Search Behavior")

if 'uploaded_df' not in st.session_state:
    st.info("Upload your History file to view this page.")
else:
    if 'raw_session_data' not in st.session_state:
        st.error("raw session data not in cache!")
    elif 'raw_visit_data' not in st.session_state:
        st.error("raw visit data not in cache!")
    else:
        render_wordcloud(st.session_state.raw_visit_data)
        render_query_table(st.session_state.raw_visit_data) #display behavior based on visits, not sessions