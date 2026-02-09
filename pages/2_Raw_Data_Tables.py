import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title = "View your Raw Browsing Data", layout="wide")

# --------------------------------
# FUNCTIONS: RENDER RAW TABLE AND STATS BAR
# --------------------------------

#raw table of results (all visits/browsing sessions for all links)
def render_raw_table(df):
    if not df.empty:
        columns_order = ["domain", "title", "url", "session_length", "session_start", "session_end", "visit_count"]
        display_cols = [c for c in columns_order if c in df.columns]

        if display_cols:
            st.dataframe(df[display_cols], width='stretch', hide_index=True)
        else:
            st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No browsing data to show.")

#render stats bar for a raw table
def render_stats_bar(df):
    col1, col2, col3 = st.columns([0.3,0.3,0.4])
    with col1:
        st.write(f"**Total logged browsing sessions:**  {len(df)}") #total # history entries
    with col2:
        st.write(f"**Unique domains:** {df['domain'].nunique()}")
    with col3:
        st.write(f"**Timeframe:** {df['session_start'].min()} to {df['session_end'].max()}")
    return

def render_raw_data():
    if 'raw_session_data' not in st.session_state:
        st.error("raw session data not in cache!")
    if 'raw_visit_data' not in st.session_state:
        st.error("raw visit data not in cache!")
    
    raw_visit_data = st.session_state.raw_visit_data    #get data from cache
    raw_session_data = st.session_state.raw_session_data
    uploaded_df = st.session_state.uploaded_df

    #VIEW FILTERED BROWSING DATA
    st.markdown("View a table of all your browsing sessions below! All keyword filters have been applied.")

    render_stats_bar(raw_session_data)
    st.info("""Review your filtered data below. Each row represents a browsing session of 30 minutes or less. You can sort columns by clicking headers.""")
        
    #render raw table
    render_raw_table(raw_session_data)
    st.markdown("---")

st.markdown("## **View your Raw Data**")

if 'uploaded_df' not in st.session_state:
    st.info("Upload your History file to view this page.")
else:
    render_raw_data()