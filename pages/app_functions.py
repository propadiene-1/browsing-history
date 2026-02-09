import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta
import altair as alt

# ----------------------------
# Chrome History file handling
# ----------------------------

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

#load SQLite db from safari to a pandas df
def load_safari_history_db(db_path):
    conn = sqlite3.connect(db_path)
    query = """ 
        SELECT
            id,
            title,
            visit_time
        FROM history_visits as visits
        ORDER BY visits.visit_time
    """ #join urls by visit based on id and sort
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# -------------------------------
# Raw data cleaning (browser data)
# -------------------------------

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
    df['session_length'] = df['session_end'] - df['session_start']
    return df

# ------------------------------------
# Stats and data aggregation functions
# ------------------------------------

#aggregate # of browsing sessions by domain
def aggregate_browsing_sessions(df):
    session_counts = df['domain'].value_counts().reset_index() #sum all sessions w/ same domain
    session_counts.columns = ['domain', 'total_sessions']
    return session_counts  #return df with only domain + total visits

#count domains below vs above threshold
def compute_visit_threshold_counts(session_counts, threshold=10):
    less_count = len(session_counts[session_counts['total_sessions'] < threshold]) #mask df and sum result
    more_equal_count = len(session_counts[session_counts['total_sessions'] >= threshold])

    return pd.DataFrame(
        {
            "Category": [
                f"Websites visited < {threshold} times",
                f"Websites visited ≥ {threshold} times",
            ],
            "Total Count": [less_count, more_equal_count],
        }
    )

# --------------------------------
# Render tables and visualizations
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
            y=alt.Y("total_sessions:Q", title="Browsing Sessions"),
            tooltip=["domain", "total_sessions"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, width='stretch')

#render pie chart for sites by visit threshold
def render_visit_threshold_pie_chart(threshold_df):
    if threshold_df["Total Count"].sum() == 0:
        st.info("No data available for pie chart.")
        return
    chart = (
        alt.Chart(threshold_df)
        .mark_arc()
        .encode(
            theta="Total Count:Q",
            color=alt.Color(
                "Category:N",
                legend=alt.Legend(
                    orient="left",
                    title=None,
                    padding=0,
                    rowPadding=0,
                    columnPadding=0
                )
            ),
            tooltip=["Category", "Total Count"],
        )
        .properties(width=400, height=400)
    )
    st.altair_chart(chart, width='stretch')

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
