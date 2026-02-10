import streamlit as st

st.set_page_config(page_title="About this Site", layout="wide")

st.markdown("## About this Site")

st.markdown("### Description")
st.markdown("""

This is an app for you to view and analyze your browsing history. It currently works for Chrome and Safari.

This site was greatly inspired by [the Cookies Project](https://cookiesproject.streamlit.app/) made by Jessica, Nina, Crystal, and Dianna from Wellesley Cred Lab. Go check it out!

### What does this site do?

- Read your (local) Google Chrome history.
- Show you data:
  - **Raw browsing history** organized in a table of browsing sessions.
  - **Site visit frequency** in a sorted bar chart.
  - **Proportion of less-visited sites** in a pie chart with an adjustable visit threshold.
  - **List** of less frequently visited domains (based on the same threshold).
  - **Recent search queries** in a list of dropdowns, each revealing your browsing behavior after the search.

The goal is to visualize your browsing patterns and understand what kind of personal data your browser contains.

### Privacy
We do not store any of your data! Your file is stored in your current session state (the current session's memory), and will disappear when your session ends -- unless you choose to share it with us using the "share data" page.

### Authors
Made by the Wellesley Cred Lab. Led by Aileen Liang, advised by Prof. Eni Mustafaraj.
""")