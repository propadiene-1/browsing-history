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
    with col3:   #split into cases based on the table
        if 'session_start' in df and 'session_end' in df:
            st.write(f"**Timeframe:** {df['session_start'].min()} to {df['session_end'].max()}")
        elif 'visit_time' in df:
            st.write(f"**Timeframe:** {df['visit_time'].min()} to {df['visit_time'].max()}")
        else:
            return
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

    st.markdown("### Raw Data (Browsing Sessions)")

    render_stats_bar(raw_session_data)
    st.info("""Each row represents a browsing session of 30 minutes or less. You can sort columns by clicking headers.""")
    
    #ADD INFO: the visit_count on the right is the # of visits within the same session.

    #render raw table
    render_raw_table(raw_session_data)

    with st.expander("Details for how we tracked the browsing sessions", expanded=False):
        st.markdown("""
        As a user, you might click between dozens of tabs within a single 10-to-20 minute interval. 
        Each click triggers a domain change, so your browser logs every click as a "new visit".  
        
        Instead of logging individual clicks, we log "sessions" by grouping clicks to each domain in 30-minute intervals. Our goal is to estimate how often you realistically go back to a website, instead of how often you click between tabs.  

        **For Example:** If you click 'domain 1'/'tab1' , and then click to 'tab 2', and come back to 'tab 1' within 30 minutes, we log both clicks on 'tab 1' within the same "browsing session." 
        However, if 'tab 1' has not been clicked for over 30 minutes and then you come back, it will start a new browsing session (a new "visit.")  

        However, you can still view your data in **visits** (raw clicks) below!
        """)

    st.markdown("### Raw Data (Clicks)")
    render_stats_bar(raw_visit_data)
    st.info("""Each row represents a click to a domain. You can sort columns by clicking headers.""")
    columns_order = ["domain", "title", "url", "visit_time"]
    display_cols = [c for c in columns_order if c in raw_visit_data.columns]
    if display_cols:
        st.dataframe(raw_visit_data[display_cols], width='stretch', hide_index=True)
    else:
        st.dataframe(raw_visit_data, width='stretch', hide_index=True)

st.markdown("## **View your Raw Data**")

if 'uploaded_df' not in st.session_state:
    st.info("Upload your History file to view this page.")
else:
    render_raw_data()