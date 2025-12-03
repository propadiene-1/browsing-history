import streamlit as st

st.title("ℹ️ About Chrome History Explorer")

st.markdown("""
This is an app for you to view your browsing history!

### what does it do?
- Read your local Google Chrome history.
- Show you data:
  - a raw table of your history.
  - a bar chart of sites, by # of visits.
  - a pie chart showing how many sites are **less frequently visited** (you select the frequency threshold!)
  - a table of those less frequently visited sites.

The goal is to show you how many sites you actually don't visit often!

### Privacy
- We do **NOT** store any of your data!
- Your file is only in the current session's memory. It is not stored or sent anywhere else.
""")