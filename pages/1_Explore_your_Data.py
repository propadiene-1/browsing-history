import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta
import altair as alt

#add parent directory to path to import app_functions
#import sys
#from pathlib import Path
#sys.path.append(str(Path(__file__).parent.parent))
from app_functions import *

st.set_page_config(page_title = "Explore your Data", layout="wide")

# ------------------
# Download Filtering
# ------------------

#@st.dialog("Prepare Data", *, width="small", dismissible=True, icon=None, on_dismiss="ignore")
#if st.button("Download blah blah")
#prepare_download(session_counts)
#def prepare_download(df): #filter df using keywords to prep for download

# --------------------------
# Render data visualizaitons
# --------------------------

def render_data():

    df = pd.DataFrame()  # initialize empty df
    
    if 'raw_session_data' not in st.session_state:
        st.error("raw session data not in cache!")
    if 'raw_visit_data' not in st.session_state:
        st.error("raw visit data not in cache!")
    
    #get data from cache
    df = st.session_state.df
    raw_session_data = st.session_state.raw_session_data
    raw_visit_data = st.session_state.raw_visit_data

    #STEP 3 VISUAL CHARTS

    #st.subheader("Step 3: Visualize your Data")
    aggregate_sessions_data = aggregate_browsing_sessions(raw_session_data) #aggregate all sessions per domain

    #DOWNLOAD TOP DOMAINS (CSV)
    aggregate_sessions_data.sort_values(['total_sessions'])
    top_1000_domains = aggregate_sessions_data.head(1000) #top 1000 most visited domains
    csv_data = top_1000_domains.to_csv()

    #RENDER BAR CHART
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("#### Most Frequently Visited Domains")
    with col2: 
        st.download_button(     #download button (csv)
            label="Download top 1000 domains (CSV)",
            data=csv_data,
            file_name=f"top_1000_domains.csv",
        )

    if len(aggregate_sessions_data) == 0:
        st.warning("There are no sessions in your browsing history to display.")
        return

    #BAR CHART SLIDER (for # sites to display)
    top_n = 50
    top_n = st.slider("Number of domains", 5, 100, top_n, 5)

    render_domain_bar_chart(aggregate_sessions_data, top_n)

    #RENDER PIE CHART
    st.markdown("#### Percentage of Highly-Visited Domains")
    col1, col2 = st.columns([1, 0.8])
    
    threshold = 10 #domain visit threshold input adjuster
    with col1:
        threshold = st.number_input("Adjust visit threshold", 1, 1000, 10, 1, width=200)
        threshold_df = compute_visit_threshold_counts(aggregate_sessions_data, threshold) #just stores below count, above count
        render_visit_threshold_pie_chart(threshold_df) #render with threshold

    #RENDER TOTAL PERCENT (BELOW AND ABOVE THRESHOLD)
    total_domains = len(aggregate_sessions_data)
    below_count = threshold_df[threshold_df["Category"] == f"Websites visited < {threshold} times"]['Total Count'].iloc[0]
    above_count = total_domains - below_count

    percent_below = round((below_count / total_domains) * 100, 2)
    percent_above = round((above_count / total_domains) * 100, 2)

    with col2:
        st.markdown(
            f"""
            ### You visited :blue[{percent_below}%] of the sites in your browser history less than :blue[{threshold}] times.
            """)
        
        domains_below = aggregate_sessions_data[aggregate_sessions_data['total_sessions'] < threshold] #mask df with only rows < threshold

        #DISPLAY LIST (less-visited sites)
        if len(domains_below) > 0:
            st.dataframe(domains_below, width='stretch', hide_index=True)
        else:
            st.write("No domains fall below this threshold.")
        
        st.write(f"**Total:** {len(domains_below)} domains")

    #ADD EXPLANATION BELOW
        
    st.markdown("---")

    #STEP 4 VIEW YOUR SEARCH BEHAVIOR
    #st.subheader("Step 4: View Your Search Behavior")

    st.markdown("#### Recent Search Behavior")
    render_query_table(raw_visit_data)
    

st.markdown("## **Explore your Data**")

if 'df' not in st.session_state:
    st.info("Please upload your History file.")
else:
    render_data()
#def main():
#   st.set_page_config(page_title="Explore your Data", layout="wide")
#   st.set_page_config(page_title="Browser History Analyzer", layout="wide")

#if __name__ == "__main__":
#    main()