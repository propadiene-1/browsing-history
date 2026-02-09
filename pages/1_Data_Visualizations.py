import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title = "Explore your Browsing Data", layout="wide")

# ------------------
# Download Filtering
# ------------------

#@st.dialog("Prepare Data", *, width="small", dismissible=True, icon=None, on_dismiss="ignore")
#if st.button("Download blah blah")
#prepare_download(session_counts)
#def prepare_download(df): #filter df using keywords to prep for download

# ----------------------------------------------
# FUNCTIONS: PREP FOR PIE CHART: COUNTING VISITS
# ----------------------------------------------

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

# -----------------------------------------------
# FUNCTION: RENDER PIE CHART (by visit threshold)
# -----------------------------------------------

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

# ------------------------------------------------
# FUNCTION: RENDER BAR CHART (domains by # visits)
# ------------------------------------------------

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

# --------------------------
# Render data visualizations
# --------------------------

def render_data():

    df = pd.DataFrame()  # initialize empty df
    
    if 'raw_session_data' not in st.session_state:
        st.error("raw session data not in cache!")
    if 'raw_visit_data' not in st.session_state:
        st.error("raw visit data not in cache!")
    
    #get data from cache
    uploaded_df = st.session_state.uploaded_df
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
    

st.markdown("## **Visualize your Browsing Data**")

if 'uploaded_df' not in st.session_state:
    st.info("Upload your History file to view this page.")
else:
    render_data()
#def main():
#   st.set_page_config(page_title="Explore your Data", layout="wide")
#   st.set_page_config(page_title="Browser History Analyzer", layout="wide")

#if __name__ == "__main__":
#    main()