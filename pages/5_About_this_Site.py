import streamlit as st

st.set_page_config(page_title="About this Site", layout="wide")

st.markdown("## About this Site")

st.markdown("### Description")
st.markdown("""

This is an app for you to view your browsing history!

This site was greatly inspired by [the Cookies Project](https://cookiesproject.streamlit.app/) made by Jessica, Nina, Crystal, and Dianna from Wellesley Cred Lab. Go check it out!

### What does it do?

This app will:
- Read your (local) Google Chrome history.
- Show you data:
  - **Raw browsing history** organized in a table of browsing sessions.
  - **Site visit frequency** in a sorted bar chart.
  - **Proportion of less-visited sites** in a pie chart with an adjustable visit threshold.
  - **List** of less frequently visited domains (based on the same threshold).
  - **Recent search queries** in a list of dropdowns, each revealing your browsing behavior after the search.

The goal is to see how many sites you actually don't visit often!

### Privacy
We do **NOT** store any of your data! Your file is only in the current session's memory. It is not stored or sent anywhere else, unless you choose to send it to us with the "share data" page.

### Authors
Made by the Wellesley Cred Lab. Led by Aileen Liang, advised by Prof. Eni Mustafaraj.
""")