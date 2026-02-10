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
            visits.visit_time,
            urls.visit_count
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