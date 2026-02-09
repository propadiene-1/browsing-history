import streamlit as st 
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta
from app_functions import *

st.set_page_config(page_title = "Home", layout="wide")

#CONVERT FILE TO DF
def convert_to_df(uploaded_file):
    #process file into df
    try:
        temp_path = save_uploaded_file_to_temp(uploaded_file)
        df = load_chrome_history_db(temp_path)
    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")
    return

#KEYWORD FILTERING
def filter_data(df, keywords): #keywords stored as a dic
    dropped_indices = []
    for index, row in df.iterrows():
        for keyword in keywords.keys():
            if row.astype(str).str.contains(keyword, case=False).any(): #case-insensitive, column-insensitive
                dropped_indices.append(index)
                break
    return df.drop(dropped_indices) # drop once at end for efficiency

def render_instructions():

    st.markdown("""
    ### Exclude domains
    Before uploading your data, you can list any number of keywords in this box to exclude. Any domain, search, or url which contains the keyword will be removed. 
    
    We will not save your keywords anywhere.
    """)

    st.info("**IMPORTANT:** Keywords must be comma-separated (including the ending). EX: chatgpt, gemini, claude,")

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

    st.markdown("### Upload your History File to Get Started.")
    
    st.write("Instructions to get your History file below.")
    st.info("**NOTE:** Check that you have closed your browser (e.g. Google Chrome) before uploading your data.")
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
    **NOTE:** Your file will not be sent anywhere! It is stored in the temporary streamlit cache (disappears with Cmd/Ctrl + R).
    """)

st.markdown("## Welcome!")

render_instructions()

#FILE PROCESSING
uploaded_file = st.file_uploader(   #render the file uploader
    "placeholder label to avoid error",
    label_visibility="collapsed",
    type=None,
)
if uploaded_file is None:
    st.warning("Please upload the file to proceed.")
else:
    try:  #PROCESS FILE INTO A DF
        temp_path = save_uploaded_file_to_temp(uploaded_file)
        df = load_chrome_history_db(temp_path)
        df = filter_data(df, st.session_state.keywords) #filter out keywords

        if df.empty:    #check for empty after filtering
            st.error("There is no browsing data in this file.")
        else:
            st.session_state.uploaded_df = df    #checkpoint: store user-uploaded history in a df

            df = add_domain(df)
            df["visit_time"] = df["visit_time"].apply(chrome_time_to_datetime) #human-readable time
            st.session_state.raw_visit_data = df                  #checkpoint: save raw visit data
                
            df = split_sessions(df)     #record sessions > visits
            df = add_session_length(df)

            st.session_state.raw_session_data = df       #checkpoint: save raw data in sessions

    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")