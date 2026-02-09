import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title = "Understand your Recent Search Behavior", layout="wide")

# ------------------------
# VISUALIZE SEARCH RESULTS
# ------------------------

#shows 5 searches after a query
def render_query_table(raw_data, limit=40):
    
    raw_data = raw_data.sort_values(by='visit_time').reset_index(drop=True)
    query_indices = raw_data[raw_data['title'].str.contains('Google Search', na=False)].index #mask with google search

    if len(query_indices) == 0:
        st.info("No google searches were found in your history.")
        return
    st.info(f"Showing {min(limit, len(query_indices))} of your most recent Google searches. Click to see your browsing behavior after the search!")

    #only go up to the last [limit] searches
    recent_searches = query_indices[::-1][:limit]

    for search_index in recent_searches:
        row = raw_data.iloc[search_index] #look up query in full data table
        search_title = row['title'].replace('- Google Search', '')
        search_results = raw_data.iloc[search_index+1 : search_index+6][['visit_time', 'domain', 'url', 'title']]
        
        with st.expander(f"{search_title} | {row['visit_time']}"): #display in streamlit
            st.dataframe(search_results, hide_index=True, width='stretch')
    return

st.markdown("## Explore your Search Behavior")

if 'uploaded_df' not in st.session_state:
    st.info("Upload your History file to view this page.")
else:
    if 'raw_session_data' not in st.session_state:
        st.error("raw session data not in cache!")
    elif 'raw_visit_data' not in st.session_state:
        st.error("raw visit data not in cache!")
    else:
        render_query_table(st.session_state.raw_visit_data) #display behavior based on visits, not sessions