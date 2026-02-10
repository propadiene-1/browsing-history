import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title = "Explore your Browsing Data", layout="wide")

# HEATMAP

def create_hourly_heatmap():
    """
    Create a heatmap showing visits by hour of day and date
    """
    # Check if data exists
    if 'raw_visit_data' not in st.session_state:
        st.warning("Please upload your browsing history first!")
        return
    
    df = st.session_state.raw_visit_data.copy()
    
    if df.empty:
        st.warning("No visit data available.")
        return
    
    # Step 1: Extract hour and date from each visit
    df['hour'] = df['visit_time'].dt.hour  # Gets 0-23
    df['date'] = df['visit_time'].dt.date   # Gets just the date (no time)
    
    # Step 2: Count how many visits happened at each hour on each date
    # This groups all visits by date AND hour, then counts them
    # Example: 5 visits on 2024-01-15 at 14:00 becomes one row with count=5
    heatmap_data = df.groupby(['date', 'hour']).size().reset_index(name='visit_count')
    
    # Step 3: Fill in missing hours with 0 visits
    # If you didn't visit anything at 3am on a certain day, we still want to show 0
    all_dates = pd.DataFrame({'date': df['date'].unique()})  # All unique dates
    all_hours = pd.DataFrame({'hour': range(24)})             # 0 through 23
    all_combinations = all_dates.merge(all_hours, how='cross')  # Every date × every hour
    
    # Merge with actual data, fill missing with 0
    heatmap_data = all_combinations.merge(
        heatmap_data, 
        on=['date', 'hour'], 
        how='left'
    ).fillna(0)
    
    # Step 4: Format date as string for display
    heatmap_data['date_str'] = pd.to_datetime(heatmap_data['date']).dt.strftime('%Y-%m-%d')
    
    # Step 5: Create the heatmap visualization
    chart = alt.Chart(heatmap_data).mark_rect().encode(
        # X-axis: dates across the bottom
        x=alt.X('date_str:N', title='Date', axis=alt.Axis(labelAngle=-45)),
        
        # Y-axis: hours down the side (midnight at top, 11pm at bottom)
        y=alt.Y('hour:O', 
                title='Hour of Day',
                sort='descending',  # Makes 0 (midnight) appear at top
                axis=alt.Axis(
                    labelExpr='datum.value + ":00"',  # Shows "14:00" instead of "14"
                    labelAngle=0
                )),
        
        # Color: darker blue = more visits
        color=alt.Color(
            'visit_count:Q',
            title='Visits',
            scale=alt.Scale(scheme='blues')
        ),
        
        # Tooltip: what you see when you hover
        tooltip=[
            alt.Tooltip('date_str:N', title='Date'),
            alt.Tooltip('hour:O', title='Hour'),
            alt.Tooltip('visit_count:Q', title='Visits')
        ]
    ).properties(
        width=800,
        height=600,
        title='Browsing Activity Heatmap by Hour'
    )
    
    st.altair_chart(chart, use_container_width=True)
    
    # Summary statistics
    st.markdown("### Activity Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        busiest_hour = df['hour'].mode()[0] if not df.empty else 0
        st.metric("Most Active Hour", f"{busiest_hour:00d}:00")
    
    with col2:
        total_visits = len(df)
        st.metric("Total Visits", f"{total_visits:,}")
    
    with col3:
        avg_per_hour = df.groupby('hour').size().mean()
        st.metric("Avg Visits/Hour", f"{avg_per_hour:.1f}")

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

def render_stats_bar(df): #stats bar for bar chart
    col1, col2, col3 = st.columns([0.3,0.3,0.4])
    with col1:
        st.write(f"**Total logged browsing sessions:**  {len(df)}") #total # history entries
    with col2:
        st.write(f"**Unique domains:** {df['domain'].nunique()}")
    with col3:   #split into cases based on the table
        if 'session_start' in df and 'session_end' in df:
            st.write(f"**Timeframe:** {df['session_start'].min()} to {df['session_end'].max()}")
        elif 'visit_time' in df:
            st.write(f"**Timeframe:** {df['visit_time'].min()} to {df['visit_time'].max()}")
        else:
            return
    return
# -------------------------------------------------------------
# FUNCTION: RENDER HEAT MAP (Most common browsing times per day)
# -------------------------------------------------------------

# --------------------------
# Render data visualizations
# --------------------------

def render_data():

    df = pd.DataFrame()  # initialize empty df

    if 'browsing_session_counts' in st.session_state:
        aggregate_sessions_data = st.session_state.browsing_session_counts   #get data from cache
    else:
        st.error("browsing_session_counts is not in the session state.")
    
    #DOWNLOAD TOP DOMAINS (CSV)
    aggregate_sessions_data.sort_values(['total_sessions'])
    top_1000_domains = aggregate_sessions_data.head(1000) #top 1000 most visited domains
    csv_data = top_1000_domains.to_csv()

    # ---------------------
    # RENDER BAR CHART
    # ---------------------

    aggregate_sessions_data.sort_values('total_sessions')

    st.markdown("#### Top 3 Domains")
    cols = st.columns([1,1,1])
    for i, col in enumerate(cols):
        with col:
            domain = aggregate_sessions_data.iloc[i, 0]
            st.markdown(
                f'<p style="font-size: 32px; color: #0068c9; font-weight: 600; text-align: center;">{domain}</p>',
                unsafe_allow_html=True
            )#ADD8E6
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### Most Frequently Visited Domains")
    with col2: 
        st.download_button(     #download button (csv)
            label="Download top 1000 domains (CSV)",
            data=csv_data,
            file_name=f"top_1000_domains.csv",
        )

    render_stats_bar(raw_session_data)

    if len(aggregate_sessions_data) == 0:
        st.warning("There are no sessions in your browsing history to display.")
        return

    #BAR CHART SLIDER (for # sites to display)
    top_n = 50
    top_n = st.slider("Number of domains", 5, 100, top_n, 5)

    render_domain_bar_chart(aggregate_sessions_data, top_n)

    # ------------------
    # RENDER PIE CHART
    # ------------------

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
    if 'raw_session_data' not in st.session_state:
        st.error("raw session data not in cache!")
    elif 'raw_visit_data' not in st.session_state:
        st.error("raw visit data not in cache!")
    else: 
        #get data from cache
        uploaded_df = st.session_state.uploaded_df
        raw_session_data = st.session_state.raw_session_data
        raw_visit_data = st.session_state.raw_visit_data

        #aggregate the data and save to cache
        st.session_state.browsing_session_counts = aggregate_browsing_sessions(raw_session_data)

        #render visualizations
        render_data()

        # Call this function in your Streamlit page
        st.markdown("### Browsing Activity Heatmap")
        create_hourly_heatmap()