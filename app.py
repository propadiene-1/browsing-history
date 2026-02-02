import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta
import altair as alt
from app_functions import *

# ------------------------
# Render user instructions
# ------------------------

def filter_data(df, keywords): #keywords stored as a dic
    dropped_indices = []
    for index, row in df.iterrows():
        for keyword in keywords.keys():
            if row.astype(str).str.contains(keyword, case=False).any(): #case-insensitive, column-insensitive
                dropped_indices.append(index)
                break
    return df.drop(dropped_indices) #drop once at end for efficiency

def convert_to_df(uploaded_file):
    #process file into df
    try:
        temp_path = save_uploaded_file_to_temp(uploaded_file)
        df = load_chrome_history_db(temp_path)
    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")
    return

def render_instructions():

    st.markdown("""
    ### Step 1: Exclude domains
    Before uploading your data, you can list any number of keywords in this box to exclude. Any domain, search, or url which contains the keyword will be removed. 
    
    We will not save your keywords anywhere.
    """)

    st.info("**NOTE:** Keywords must be comma-separated.")

    user_input = st.text_area(
        "placeholder label",
        max_chars=None,
        on_change=None, 
        placeholder="Enter keywords...", 
        disabled=False, 
        label_visibility="collapsed", 
        width="stretch")

    if 'keywords' not in st.session_state: #save keywords into dic for this session
        st.session_state.keywords = {}

    if st.button("Save keywords"): #submit button auto-saves text box
        if user_input:
            items = [line.strip() for line in user_input.split(',') if line.strip()]
            st.session_state.keywords = {i: 0 for i in items}     #store input as keywords
            st.success(f"**SAVED KEYWORDS:** {user_input}")
        else:
            st.error("Please enter keywords to save.")

    st.markdown("### Step 2: Upload and Review your History File")
    
    st.write("Instructions to get your History file")
    st.info("**IMPORTANT:**  Make sure you have closed Google Chrome before uploading your data.")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Windows")
        st.markdown("""

        1. Open file explorer

        2. %LOCALAPPDATA%\\Google\\Chrome\\User Data\\

        3. Choose either 'Default' or 'Profile 1', 'Profile 2', etc.

        4. **Drag and Drop:** 'History'"""
        )

    with col2:
        st.markdown("#### macOS")
        st.markdown("""

        1. Open Finder
        
        2. Command + Shift + G

        3. ~/Library/Application Support/Google/Chrome/

        4. Choose either 'Default' or 'Profile 1', 'Profile 2', etc.

        5. **Drag and Drop:** 'History'
        """
        )
    
    st.markdown("""##### Upload your file below!""")

    st.info("""
    **NOTE:** The table below is NOT sent or stored anywhere except your temporary cache.
    """)

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

    #FILE PROCESSING (COPIED FROM MAIN APP)
    uploaded_file = st.file_uploader(   #render the file uploader
        "placeholder label to avoid error",
        label_visibility="collapsed",
        type=None,
    )
    if uploaded_file is None:
        st.warning("Please upload the file to proceed.")
        return
    
    try:  #PROCESS FILE INTO A DF
        temp_path = save_uploaded_file_to_temp(uploaded_file)
        df = load_chrome_history_db(temp_path)      #load SQLite to pandas df
    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")
        return
    
    #data cleaning for df
    df = filter_data(df, st.session_state.keywords) #filter data
    df = add_domain(df)
    df["visit_time"] = df["visit_time"].apply(chrome_time_to_datetime) #human-readable time
    raw_data = df                  #save raw visit data
    df = split_sessions(df)     #record sessions > visits
    df = add_session_length(df)

    st.markdown("---")

    #VIEW FILTERED BROWSING DATA
    st.subheader("Your Filtered Browsing Data")

    #render overall stats bar
    col1, col2, col3 = st.columns([0.3,0.3,0.4])
    with col1:
        st.write(f"**Total logged browsing sessions:**  {len(df)}") #total # history entries
    with col2:
        st.write(f"**Unique domains:** {df['domain'].nunique()}")
    with col3:
        st.write(f"**Timeframe:** {df['session_start'].min()} to {df['session_end'].max()}")

    st.info("""Review your filtered data below. Each row represents a browsing session of 30 minutes or less. You can sort columns by clicking headers.""")

    #render raw table
    render_raw_table(df)

    st.markdown("---")

    #STEP 3 VISUAL CHARTS

    st.subheader("Step 3: Visualize your Data")
    
    session_counts = aggregate_browsing_sessions(df) #aggregate all visits per domain

    #DOWNLOAD TOP DOMAINS (CSV)
    session_counts.sort_values(['total_visits'])
    top_1000_domains = session_counts.head(1000) #top 1000 most visited domains
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

    if len(session_counts) == 0:
        st.warning("There are no sessions in your browsing history to display.")
        return

    #BAR CHART SLIDER (for # sites to display)
    top_n = 20
    top_n = st.slider("Number of domains", 5, 100, top_n, 5)

    render_domain_bar_chart(session_counts, top_n)

    #RENDER PIE CHART
    st.markdown("#### Percentage of Highly-Visited Domains")
    col1, col2 = st.columns([1, 0.8])
    
    threshold = 10 #domain visit threshold input adjuster
    with col1:
        threshold = st.number_input("Adjust visit threshold", 1, 1000, 10, 1, width=200)
        threshold_df = compute_visit_threshold_counts(session_counts, threshold) #just stores below count, above count
        render_visit_threshold_pie_chart(threshold_df) #render with threshold

    #RENDER TOTAL PERCENT (BELOW AND ABOVE THRESHOLD)
    total_domains = len(session_counts)
    below_count = threshold_df[threshold_df['category'] == f"visited < {threshold} times"]['count'].iloc[0]
    above_count = total_domains - below_count

    percent_below = round((below_count / total_domains) * 100, 2)
    percent_above = round((above_count / total_domains) * 100, 2)

    with col2:
        st.markdown(
            f"""
            ### You visited :blue[{percent_below}%] of the sites in your browser history less than :blue[{threshold}] times.
            """)
        
        domains_below = session_counts[session_counts['total_visits'] < threshold] #mask df with only rows < threshold

        #DISPLAY LIST (less-visited sites)
        if len(domains_below) > 0:
            st.dataframe(domains_below, width='stretch', hide_index=True)
        else:
            st.write("No domains fall below this threshold.")
        
        st.write(f"**Total:** {len(domains_below)} domains")
        
    st.markdown("---")

    #STEP 4 VIEW YOUR SEARCH BEHAVIOR
    st.subheader("Step 4: View Your Search Behavior")

    render_query_table(raw_data)
    
# -------------------------
# Launch the app
# -------------------------

def main():
    st.markdown("## **Explore your Data**")
    st.set_page_config(page_title="Explore your Data", layout="wide")
    render_instructions() #STEP 1
    render_data() #STEP 2-4

if __name__ == "__main__":
    main()