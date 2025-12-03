import streamlit as st

st.markdown("### About this site (browsing history visualizer)")

st.markdown("""
This is an app for you to view your browsing history!

#### what does it do?
- Read your (local) Google Chrome history.
- Show you data:
  - **Raw table** of your history.
  - **Bar chart** of sites, by # of visits.
  - **Pie chart** showing how many sites are **less frequently visited** (you select the frequency threshold!)
  - **List** of those less frequently visited sites.

The goal is to see how many sites you actually don't visit often!

#### privacy
- We do **NOT** store any of your data!
- Your file is only in the current session's memory. It is not stored or sent anywhere else.
""")