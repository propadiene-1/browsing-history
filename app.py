import streamlit as st
import pandas as pd
import sqlite3
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timedelta
import altair as alt

# ----------------------
# Data Processing util
# ----------------------

#save streamlit file to temp file on disc
def save_uploaded_file_to_temp(uploaded_file):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(uploaded_file.read())
    tmp.close()
    return tmp.name

#load SQLite DB from chrome into a pandas df
def load_chrome_history_db(db_path):
    conn = sqlite3.connect(db_path)
    query = """
        SELECT
            url,
            title,
            visit_count,
            typed_count,
            last_visit_time
        FROM urls
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#convert chrome timestamps to human-readable date time
#Chrome uses microseconds since 1601-01-01 UTC
def chrome_time_to_datetime(chrome_time):
    if pd.isna(chrome_time):
        return None

    try:
        epoch_start = datetime(1601, 1, 1)
        return epoch_start + timedelta(microseconds=int(chrome_time))
    except:
        return None

#add human-readable domain column
def add_domain(df):
    df = df.copy()

    #get domain name
    def extract_domain(url):
        if not isinstance(url, str):
            return ""
        parsed = urlparse(url)
        dom = parsed.netloc.split(":")[0]
        if dom.startswith("www."):
            dom = dom[4:]
        return dom

    df["domain"] = df["url"].apply(extract_domain)
    return df

#aggregate visit_count column by domain
def aggregate_domain_stats(df):
    df_valid = df[df["domain"].astype(bool)].copy()

    domain_counts = (
        df_valid.groupby("domain")["visit_count"]
        .sum()
        .reset_index()
        .rename(columns={"visit_count": "total_visits"})
        .sort_values("total_visits", ascending=False)
    )
    return domain_counts

#count domains below vs above threshold
def compute_visit_threshold_counts(domain_counts, threshold=10):

    less_mask = domain_counts["total_visits"] < threshold
    less_count = less_mask.sum()
    more_equal_count = (~less_mask).sum()

    return pd.DataFrame(
        {
            "category": [
                f"visited < {threshold} times",
                f"visited ≥ {threshold} times",
            ],
            "count": [less_count, more_equal_count],
        }
    )


# -------------------------
# Rendering Visualizations
# -------------------------

#raw table of results (all visits for all links)
def render_raw_table(df):

    columns_order = ["url", "domain", "title", "visit_count", "last_visit", "typed_count"]
    display_cols = [c for c in columns_order if c in df.columns]

    if display_cols:
        st.dataframe(df[display_cols], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

#bar chart of domains ranked by times visited
def render_domain_bar_chart(domain_counts, top_n=20):

    if domain_counts.empty:
        st.info("No domain data to show.")
        return

    top_domains = domain_counts.head(top_n)

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

    st.altair_chart(chart, use_container_width=True)

#pie chart for sites visited <= n or > n times
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

    st.altair_chart(chart, use_container_width=True)


# ------------------------------
# Instructions for user (Step 1)
# ------------------------------

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


# ----------------------------------
# Data Visualizations (Step 2 and 3)
# ----------------------------------

def render_data():

    #file upload
    uploaded_file = st.file_uploader("",
        type=None,
    )

    if uploaded_file is None:
        st.warning("Please upload the file to proceed.")
        return
    
    #process file into df w/ function modifications
    try:
        temp_path = save_uploaded_file_to_temp(uploaded_file)
        df = load_chrome_history_db(temp_path)
        df = add_domain(df)
        #change last_visit_time to human-readable date times
        df["last_visit"] = df["last_visit_time"].apply(chrome_time_to_datetime)
    
    except Exception as e:
        st.error(f"Unable to read the file. Error: {e}")
        return

    #Step 2: raw table
    st.subheader("Step 2: View your Raw History Data")
   
    #overall stats
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total history entries:**  {len(df):,}")
    with col2:
        st.write(f"**Unique domains:** {df['domain'].nunique():,}")

    st.info("You can sort columns by clicking headers.")

    #render the table
    render_raw_table(df)

    st.markdown("---")

    #Step 3: bar chart and pie chart

    st.subheader("Step 3: Visualize your Data")
    
    #bar chart
    st.markdown("#### Domains by Frequency of Visits (Bar Chart)")
    
    #computing domain stats
    domain_counts = aggregate_domain_stats(df)

    if len(domain_counts) == 0:
        st.warning("There are no sites in your browser history to display.")
        return

    #adjust # of sites
    top_n = 20
    top_n = st.slider("Number of domains", 5, 100, top_n, 5)

    #render bar chart
    render_domain_bar_chart(domain_counts, top_n)

    #pie chart

    st.markdown("#### Visit Frequency Distribution (Pie Chart)")

    col1, col2 = st.columns([2, 1])

    #adjust threshold
    threshold = 10
    with col2:
        threshold = st.number_input("Adjust visit threshold", 1, 1000, 10, 1)

    threshold_df = compute_visit_threshold_counts(domain_counts, threshold)

    #render pie chart

    with col1:
        render_visit_threshold_pie_chart(threshold_df)

    total_domains = len(domain_counts)
    below_count = len(domain_counts[domain_counts["total_visits"] < threshold])
    above_count = total_domains - below_count

    percent_below = round((below_count / total_domains) * 100, 2)
    percent_above = round((above_count / total_domains) * 100, 2)

    with col2:
        st.markdown(
            f"""
            


            ### You visited :blue[{percent_below}%] of the sites in your browser history less than :blue[{threshold}] times.
            """)


    #top rare sites
    st.subheader("Step 4: Review Less Frequently Visited Sites")
    domains_below = domain_counts[domain_counts["total_visits"] < threshold]

    st.info("You can sort columns by clicking headers.")
    st.markdown(f"##### Websites visited fewer than {threshold} times")
    st.write(f"**Total:** {len(domains_below)} domains")

    if len(domains_below) > 0:
        st.dataframe(domains_below, use_container_width=True)
    else:
        st.write("No domains fall below this threshold.")

# -------------------------
# App Launch
# -------------------------

def main():
    st.set_page_config(page_title="Chrome History Explorer", layout="wide")

    render_instructions()

    render_data()


if __name__ == "__main__":
    main()