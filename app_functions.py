import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
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

#detect the browser of the history file (based on db titles)
#might create weird errors for Opera, etc. because they have the same naming conventions as chrome
def detect_browser(db_path):
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'" #select all tables
    )}
    conn.close()
    if "urls" in tables and "visits" in tables:
        return "chrome"
    elif "history_items" in tables and "history_visits" in tables:
        return "safari"
    #elif "moz_places" in tables and "moz_historyvisits" in tables:
    #    return "firefox"
    else:
        st.error("Could not successfully interpret your file. App is currently not compatible with this browser.")
        return "unknown"

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
    #urls.visit_count
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#helper for safari variants, make dictionary of columns
def _cols(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}

#load SQLite db from safari to a pandas df (chrome format)
def load_safari_history_db(db_path):
    conn = sqlite3.connect(db_path)
    #handle safari variants (items and visits)
    items_cols  = _cols(conn, "history_items")
    visits_cols = _cols(conn, "history_visits")
    if "title" in items_cols:
        title_expr = "items.title"
    elif "title" in visits_cols:
        title_expr = "visits.title"
    elif "page_title" in visits_cols:
        title_expr = "visits.page_title"
    else:
        title_expr = "NULL"
    query = f""" 
        SELECT
            items.url AS url,
            {title_expr} AS title,
            visits.visit_time AS visit_time,
            counts.visit_count AS visit_count
        FROM history_visits AS visits
        JOIN history_items AS items
            ON visits.history_item = items.id
        ORDER BY visits.visit_time
    """ #join urls by visit based on id and sort
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#JOIN(
#   SELECT 
#       history_item,
#        COUNT(*) as visit_count
#        FROM history_visits
#        GROUP BY history_item
#        ) AS counts
#        ON counts.history_item = items.id

#load SQLite db from firefox to pandas df (chrome format)
def load_firefox_history_db(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("""
        SELECT
            places.url,
            places.title,
            visits.visit_date AS visit_time,
        FROM moz_places AS places
        JOIN moz_historyvisits AS visits ON visits.place_id = places.id
        ORDER BY visits.visit_time
    """, conn)
    #places.visit_count
    conn.close()
    return df
# -------------------------------
# Raw data cleaning (browser data)
# -------------------------------

#convert chrome timestamps to date time (microseconds 1601-01-01 UTC)
def chrome_time_to_datetime(chrome_timestamp):
    if pd.isna(chrome_timestamp):
        return None
    try:
        chrome_start = datetime(1601, 1, 1, tzinfo=timezone.utc)
        total_seconds = round(int(chrome_timestamp)/1_000_000) #convert to seconds
        return chrome_start + timedelta(seconds=total_seconds) #seconds since UTC 1601-01-01
    except:
        return None

#convert safari timestampes to date time 
def safari_time_to_datetime(safari_timestamp):
    if pd.isna(safari_timestamp):
        return None
    try:
        coredata_start = datetime(2001, 1, 1, tzinfo=timezone.utc)
        total_seconds = int(float(safari_timestamp))   # DROP fractions
        return coredata_start + timedelta(seconds=round(float(safari_timestamp)))
    except:
        return None

def firefox_time_to_datetime(firefox_timestamp):
    if pd.isna(firefox_timestamp):
        return None
    try:
        total_seconds = round(int(firefox_timestamp) / 1_000_000)
        return datetime.fromtimestamp(total_seconds, tz=timezone.utc)
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