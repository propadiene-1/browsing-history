import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta
import altair as alt

# -------------------------------
# Raw data cleaning (browser data)
# -------------------------------

#save streamlit file to temp file on disc
def save_uploaded_file_to_temp(uploaded_file):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(uploaded_file.read())
    tmp.close()
    return tmp.name

#load SQLite db from chrome to a pandas df
def load_chrome_history_db(db_path):
    conn = sqlite3.connect(db_path)
    query = """ 
        SELECT
            urls.url,
            urls.title,
            visits.visit_time
        FROM urls
        JOIN visits ON urls.id = visits.url
        ORDER BY visits.visit_time
    """ #join urls by visit based on id and sort
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#convert chrome timestamps to date time (microseconds 1601-01-01 UTC)
def chrome_time_to_datetime(chrome_time):
    if pd.isna(chrome_time):
        return None
    try:
        chrome_start = datetime(1601, 1, 1)
        total_seconds = round(int(chrome_time)/1_000_000) #convert to seconds
        return chrome_start + timedelta(seconds=total_seconds) #seconds since UTC 1601-01-01
    except:
        return None

def timeframe(df, col): #show timeframe and add to df
    return df[col].min().strftime("%m/%d/%Y %H:%M:%S %p"), df[col].max().strftime("%m/%d/%y %H:%M:%S %p")

#add simplified domain to a df
def add_domain(df):
    df = df.copy()

    #get domain name
    def extract_domain(url):
        if not isinstance(url, str):
            return ""
        
        if url.startswith("file://"): #user saved files
            return "Local Files"

        parsed = urlparse(url)
        dom = parsed.netloc.split(":")[0]
        if dom.startswith("www."):
            dom = dom[4:]
        return dom if dom else "Unknown"

    df["domain"] = df["url"].apply(extract_domain)
    return df

#add a row with visit length
#def add_visit_length(df):
#    df = df.copy()
#    df = df.sort_values('visit_time') #sort by earliest
#   

#build df based on sessions instead of visits
def split_sessions(df, session_length=30):
    df = df.sort_values(['domain', 'visit_time']) #group by domain and chronological sort

    current_sessions = {} #current tracked sessions. key: domain; value: {all the info}
    all_sessions = [] #all completed sessions

    #iterate thru all visits
    for index, row in df.iterrows():
        curr_domain = row['domain']
        curr_visit_time = row['visit_time']
        
        if curr_domain in current_sessions: #not a new domain
            curr_session = current_sessions[curr_domain] #get session info
            #if it's been over 30m, start new session
            if (curr_visit_time - curr_session['session_start']) > timedelta(minutes=session_length):
                all_sessions.append(curr_session) #save previous session
                current_sessions[curr_domain] = {
                    'domain': curr_domain,
                    'title': row['title'] if pd.notna(row['title']) and row['title'].strip() else 'Untitled',
                    'url': row['url'],
                    'session_start': curr_visit_time, #new session starts at curr time
                    'session_end': curr_visit_time,
                    'visit_count': 1
                }
            else: #continue extending current session
                curr_session['session_end'] = curr_visit_time
                curr_session['visit_count'] += 1
                if (curr_session['title'] == 'Untitled' or not curr_session['title']) and pd.notna(row['title']) and row['title'].strip():
                    curr_session['title'] = row['title']  #just update title to latest visit
        else: #new domain (not tracking yet)
            current_sessions[curr_domain] = {#add to tracked sessions
                'domain': curr_domain,
                'title': row['title'] if pd.notna(row['title']) and row['title'].strip() else 'Untitled',
                'url': row['url'],
                'session_start': curr_visit_time, #new session starts at curr time
                'session_end': curr_visit_time,
                'visit_count': 1
            }
    all_sessions.extend(current_sessions.values()) #add all leftover sessions
    return pd.DataFrame(all_sessions)       

#add column w/ length of session
def add_session_length(df):
    df = df.copy()
    df['session_length'] = df['session_start'] - df['session_end']
    return df

# ------------------------------------
# Stats and data aggregation functions
# ------------------------------------

#aggregate # of browsing sessions by domain
def aggregate_browsing_sessions(df):
    session_counts = df['domain'].value_counts().reset_index() #sum all sessions w/ same domain
    session_counts.columns = ['domain', 'total_visits']
    return session_counts

#count domains below vs above threshold
def compute_visit_threshold_counts(session_counts, threshold=10):
    less_count = len(session_counts[session_counts['total_visits'] < threshold]) #mask df and sum result
    more_equal_count = len(session_counts[session_counts['total_visits'] >= threshold])

    return pd.DataFrame(
        {
            "category": [
                f"visited < {threshold} times",
                f"visited ≥ {threshold} times",
            ],
            "count": [less_count, more_equal_count],
        }
    )

# --------------------------------
# Render tables and visualizations
# --------------------------------

#raw table of results (all visits/browsing sessions for all links)
def render_raw_table(df):
    columns_order = ["domain", "title", "url", "session_length", "session_start", "session_end", "visit_count"]
    display_cols = [c for c in columns_order if c in df.columns]

    if display_cols:
        st.dataframe(df[display_cols], width='stretch', hide_index=True)
    else:
        st.dataframe(df, width='stretch', hide_index=True)

#render bar chart of domains by # visits
def render_domain_bar_chart(session_counts, top_n=20):
    if session_counts.empty:
        st.info("No browsing data to show.")
        return
    top_domains = session_counts.head(top_n)
    chart = (
        alt.Chart(top_domains)
        .mark_bar()
        .encode(
            x=alt.X("domain:N", sort="-y", title="Domain"),
            y=alt.Y("total_visits:Q", title="Visits"),
            tooltip=["domain", "total_visits"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, width='stretch')

#render pie chart for sites by visit threshold
def render_visit_threshold_pie_chart(threshold_df):
    if threshold_df["count"].sum() == 0:
        st.info("No data available for pie chart.")
        return
    chart = (
        alt.Chart(threshold_df)
        .mark_arc()
        .encode(
            theta="count:Q",
            color=alt.Color(
                "category:N",
                legend=alt.Legend(
                    orient="left",
                    title=None,
                    padding=0,
                    rowPadding=0,
                    columnPadding=0
                )
            ),
            tooltip=["category", "count"],
        )
        .properties(width=400, height=400)
    )
    st.altair_chart(chart, width='stretch')

#def visualize_queries(df):


# ------------------------
# Render user instructions
# ------------------------

def render_instructions():

    st.markdown("### Step 1: Upload your History File")
    
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

# --------------------------
# Render data visualizaitons
# --------------------------

def render_data():

    #file upload
    uploaded_file = st.file_uploader(
        "placeholder label to avoid error",
        label_visibility="collapsed",
        type=None,
    )
    if uploaded_file is None:
        st.warning("Please upload the file to proceed.")
        return
    
    #process file into df (w/ modifications)
    try:
        temp_path = save_uploaded_file_to_temp(uploaded_file)
        df = load_chrome_history_db(temp_path)
        df = add_domain(df)
        #change visit_time to human-readable date times
        df["visit_time"] = df["visit_time"].apply(chrome_time_to_datetime)
        raw_data = df #save raw visit data
        #split into 30-min sessions
        df = split_sessions(df)
        df = add_session_length(df)
    
    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")
        return

    #STEP 2 RENDER RAW TABLE
    st.subheader("Step 2: View your Raw Browsing Data")

    #render overall stats bar
    col1, col2, col3 = st.columns([0.3,0.3,0.4])
    with col1:
        st.write(f"**Total logged browsing sessions:**  {len(df)}") #total # history entries
    with col2:
        st.write(f"**Unique domains:** {df['domain'].nunique()}")
    with col3:
        st.write(f"**Timeframe:** {df['session_start'].min()} to {df['session_end'].max()}")

    st.info("Each row represents a browsing session of 30 minutes or less. You can sort columns by clicking headers.")

    #render raw table
    render_raw_table(df)

    st.markdown("---")

    #STEP 3 VISUAL CHARTS

    st.subheader("Step 3: Visualize your Data")
    
    #RENDER BAR CHART
    st.markdown("#### Domains by Frequency of Visits (Bar Chart)")
    session_counts = aggregate_browsing_sessions(df) #aggregate all browsing sessions

    if len(session_counts) == 0:
        st.warning("There are no sessions in your browsing history to display.")
        return
    
    top_n = 20 #slider for # sites to display
    top_n = st.slider("Number of domains", 5, 100, top_n, 5)

    render_domain_bar_chart(session_counts, top_n)

    #RENDER PIE CHART
    st.markdown("#### Visit Frequency Distribution (Pie Chart)")
    col1, col2 = st.columns([2, 1])
    
    threshold = 10 #domain visit threshold input adjuster
    with col2:
        threshold = st.number_input("Adjust visit threshold", 1, 1000, 10, 1)
    threshold_df = compute_visit_threshold_counts(session_counts, threshold) #just stores below count, above count

    with col1:
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

    #STEP 4 LIST OF LESS VISITED SITES
    st.subheader("Step 4: Review Less Frequently Visited Sites")
    domains_below = session_counts[session_counts['total_visits'] < threshold] #mask df with only rows < threshold

    st.info("You can sort columns by clicking headers.")
    st.markdown(f"##### Websites visited fewer than {threshold} times")
    st.write(f"**Total:** {len(domains_below)} domains")

    if len(domains_below) > 0:
        st.dataframe(domains_below, width='stretch', hide_index=True)
    else:
        st.write("No domains fall below this threshold.")

# -------------------------
# Launch the app
# -------------------------

def main():
    st.set_page_config(page_title="Chrome History Explorer", layout="wide")
    render_instructions() #STEP 1
    render_data() #STEP 2-4

if __name__ == "__main__":
    main()