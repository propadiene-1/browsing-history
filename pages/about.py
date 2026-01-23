import streamlit as st

st.markdown("### About this site (browsing history visualizer)")

st.markdown("""
This is an app for you to view your browsing history!

#### What does it do?
This app will:
- Read your (local) Google Chrome history.
- Show you data:
  - **Raw browsing history** organized in a table of browsing sessions.
  - **Site visit frequency** in a sorted bar chart.
  - **Proportion of less-visited sites** in a pie chart with an adjustable visit threshold.
  - **List** of less frequently visited domains (based on the same threshold).
  - **Recent search queries** in a list of dropdowns, each revealing your browsing behavior after the search.

The goal is to see how many sites you actually don't visit often!

#### privacy
- We do **NOT** store any of your data!
- Your file is only in the current session's memory. It is not stored or sent anywhere else.
""")