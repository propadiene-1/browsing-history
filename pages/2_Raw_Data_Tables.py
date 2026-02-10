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
    st.info("""Review your filtered data below. Each row represents a browsing session of 30 minutes or less. You can sort columns by clicking headers.""")
    
    #ADD INFO: the visit_count on the right is the # of visits within the same session.

    #render raw table
    render_raw_table(raw_session_data)

    st.markdown("""
    **Details on how we tracked browsing sessions:**  

    If you're like me, you might click on dozens of tabs within 10 to 20 minutes. 
    Each click triggers a domain change, and your browser usually logs this as a "new visit".  
    
    In this table, we make some changes. Instead of logging each click, we group domains by 30-minute intervals.
    If you click "domain 1"/"tab1" , and then click to "tab 2", and come back to "tab 1" within 30 minutes, both of clicks on "tab 1" will be part of the same "browsing session." 
    However, if "tab 1" has not been clicked for over 30 minutes, and then you re-open it (or come back), it will start a new browsing session (a new "visit.")  
    
    Our goal is to approximate how often you actually visit websites, instead of how often you click between tabs.  
    """)

    st.markdown("However, you can still view your data in **visits** (raw clicks) below!")

    st.markdown("### Raw Data (Clicks)")
    render_stats_bar(raw_visit_data)
    st.info("""Each row represents a **click** to a domain. You can sort columns by clicking headers.""")
    columns_order = ["domain", "title", "url", "visit_time", "visit_count"]
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