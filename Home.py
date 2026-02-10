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
            try:
                if row.astype(str).str.contains(keyword, case=False).any(): #case-insensitive, column-insensitive
                    dropped_indices.append(index)
                    break
            except Exception as e:
                st.warning(f"Error filtering row {index}: {e}")
                continue
    return df.drop(dropped_indices) # drop once at end for efficiency

def render_chrome_instructions():
    #st.info("**NOTE:** Check that you have closed your browser before uploading your data.")
    #st.markdown("##### Instructions to upload your :blue[Google Chrome] browsing history below.")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Windows")
        st.markdown("""

        1. Open file explorer

        2. %LOCALAPPDATA%\\Google\\Chrome\\User Data\\

        3. Choose either 'Default' or 'Profile 1', 'Profile 2', etc.

        4. **Drag and Drop:** 'History'
        """
        )

    with col2:
        st.markdown("##### macOS")
        st.markdown("""

        1. Open Finder
        
        2. Command + Shift + G

        3. ~/Library/Application Support/Google/Chrome/

        4. Choose either 'Default' or 'Profile 1', 'Profile 2', etc.

        5. **Drag and Drop:** 'History'
        """
        )

def render_safari_instructions():
    #st.info("**NOTE:** Check that you have closed your browser before uploading your data.")
    #st.markdown("##### Displaying instructions for :blue[Safari]")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### macOS")
        st.markdown("""

        1. Open Finder
        
        2. Command + Shift + G

        3. ~/Library/Safari/History.db

        4. **Drag and Drop:** 'History.db'
        """
        )
        st.text("")
        st.text("")

def render_firefox_instructions():
    #st.info("**NOTE:** Check that you have closed your browser before uploading your data.")
    #st.markdown("##### Displaying instructions for :blue[Mozilla Firefox]")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Windows")
        st.markdown("""
        1. Open file explorer  

        2. %APPDATA%\\Mozilla\\Firefox\\Profiles\\  

        3. Select a profile folder ending in '.default' or '.default-release'  

        4. **Drag and Drop:** 'places.sqlite'  
        """
        )

    with col2:
        st.markdown("##### macOS")
        st.markdown("""

        1. Open Finder

        2. Command + Shift + G

        3. ~/Library/Application Support/Firefox/Profiles/

        4. Select a profile folder ending in '.default' or '.default-release'

        5. **Drag and Drop:** 'places.sqlite'
        """
        )

st.markdown("## Welcome!")
st.markdown("""
    This browsing history app is designed to help you visualize and explore your browsing history. You will learn about your own browsing habits, and find out what your browser knows about you.
    
    ### Get Started

    To get started, read the instructions below for how to **upload your history file** and **filter out keywords**. (Most large browsers - Chrome, Safari, etc. - store your history on your local device in a SQLite file. You'll need to upload this local file to analyze your data.

    Concerned about privacy? We don't keep any of your data (see "Privacy" for more information). 
    """)

st.markdown("""
#### Keyword Filtering
We know browsing history is sensitive. Before uploading your data, you can list any number of keywords in this box to exclude. Any domain, search, or url which contains the keyword will be removed. 
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
    width="stretch",
    height=60)

if 'keywords' not in st.session_state: #save keywords into dic for this session
    st.session_state.keywords = {}

st.markdown("""
**NOTE:** You can see the results of your filtering in the page titled "Raw Data Tables." To make changes, just edit the keywords and re-upload the file!
""")

if st.button("Save keywords"): #submit button auto-saves text box
    if user_input:
        items = [line.strip() for line in user_input.split(',') if line.strip()]
        st.session_state.keywords = {i: 0 for i in items}     #store input as keywords
        st.success(f"**Saved** ({user_input})")
    else:
        st.error("Please enter keywords to save.")

#HEADER FOR INSTRUCTIONS (WITH BROWSER TOGGLE)
col1, col2 = st.columns([2, 1])
with col2:
    instructions = {
        "Google Chrome": render_chrome_instructions,
        "Safari": render_safari_instructions,
        #"Mozilla Firefox": render_firefox_instructions,
    }
    #default to chrome
    if "selected_instructions" not in st.session_state:
        st.session_state.selected_instructions = "Google Chrome"
    choice = st.selectbox(
        "placeholder",
        list(instructions.keys()),
        key="selected_instructions",
        label_visibility="collapsed",
    )
with col1: 
    st.markdown(f"#### Upload your History File: :blue[{st.session_state.selected_instructions}]")

st.markdown("""Instructions for uploading your local file are below. To learn more about where your data will be stored, see the "Privacy" section.""")
instructions[st.session_state.selected_instructions]()  #call the key that correspons to the selection

st.markdown("""##### Upload your file below!""")

#FILE PROCESSING
uploaded_file = st.file_uploader(   #render the file uploader
    "placeholder label to avoid error",
    label_visibility="collapsed",
    type=None,
)
if uploaded_file is None:
    st.warning("Please upload the file to proceed.")
else:
    if uploaded_file.size > 500_000_000:  # 500MB limit
        st.error("File too large (>500MB)")
        st.stop()
    try:  #PROCESS FILE INTO A DF
        with st.spinner('Processing your browsing history... This may take a moment.'):
            df = pd.DataFrame()
            temp_path = save_uploaded_file_to_temp(uploaded_file)
            #check it's a valid SQLite file
            try:
                conn = sqlite3.connect(temp_path)
                conn.execute("SELECT 1")
                conn.close()
            except sqlite3.Error:
                st.error("Invalid SQLite database file")
                st.stop()
            browser = detect_browser(temp_path)
            st.session_state.browser = browser      #checkpoint: save browser type for later

            if browser == "chrome":
                #print("Chrome history")
                df = load_chrome_history_db(temp_path)
            elif browser == "safari":
                #print("Safari history")
                df = load_safari_history_db(temp_path)
            #elif browser == "firefox":
            #    print("Firefox")
            else:
                print("Unknown browser history database")
                st.error("Unknown browser history database.")

            if df.empty:
                st.error("There is no browsing data in this file.")
                #st.stop()
            else:
                df = filter_data(df, st.session_state.keywords) #filter out keywords

                if df.empty:    #check for empty after filtering
                    st.error("There is no browsing data in this file.")
                    #st.stop()
                else:
                    st.session_state.uploaded_df = df    #checkpoint: store user-uploaded history in a df

                    df = add_domain(df)
                    if browser == "chrome":
                        df["visit_time"] = df["visit_time"].apply(chrome_time_to_datetime) #human-readable time
                    elif browser == "safari":
                        df["visit_time"] = df["visit_time"].apply(safari_time_to_datetime) #human-readable time
                    #elif browser == "firefox":
                    #    df["visit_time"] = df["visit_time"].apply(firefox_time_to_datetime) #human-readable time
                    else:
                        print("Unknown browser, can't convert the time")
                        st.error("Unknown browser, can't convert the time")
                    
                    st.session_state.raw_visit_data = df                  #checkpoint: save raw visit data
                        
                    df = split_sessions(df)     #record sessions > visits
                    if df.empty:  # ADD THIS
                        st.error("No browsing sessions could be created from your data")
                        st.stop()
                    df = add_session_length(df)
                    st.session_state.raw_session_data = df       #checkpoint: save raw data in sessions

    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")

st.markdown("""
#### Privacy
We don't save your data or send it anywhere. After you upload your file, it is only stored within your current **session state**.   
When you refresh (Cmd/Ctrl + R) or close the tab (Cmd/Ctrl + W), the data will be cleared. (This is different from a [browser cache](https://pressidium.com/blog/browser-cache-work/#what-is-the-browser-cache), which you would need to clear manually.)

More information about session states [here](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)!
""")