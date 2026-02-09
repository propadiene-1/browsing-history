import streamlit as st
from app_functions import *

st.set_page_config(page_title = "View your Raw Data", layout="wide")

def render_raw_data():
    df = st.session_state.df    #get df from cache

    df = add_domain(df)
    df["visit_time"] = df["visit_time"].apply(chrome_time_to_datetime) #human-readable time
    st.session_state.raw_visit_data = df                  #checkpoint: save raw visit data
        
    df = split_sessions(df)     #record sessions > visits
    df = add_session_length(df)

    st.session_state.raw_session_data = df       #checkpoint: save raw data in sessions

    #VIEW FILTERED BROWSING DATA
    ##st.subheader("Your Filtered Browsing Data")
    st.markdown("View a table of all your browsing sessions below! All keyword filters have been applied.")

    render_stats_bar(st.session_state.raw_session_data)
    st.info("""Review your filtered data below. Each row represents a browsing session of 30 minutes or less. You can sort columns by clicking headers.""")
        
    #render raw table
    render_raw_table(st.session_state.raw_session_data)
    st.markdown("---")

st.markdown("## **View your Raw Data**")

if 'df' not in st.session_state:
    st.info("Please upload your History file.")
else:
    render_raw_data()