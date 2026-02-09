import streamlit as st

st.set_page_config(page_title="Share your Data", layout="wide")

st.markdown("## **Share your Data**")
st.markdown("""
This part is completely OPTIONAL. If you found the app helpful, you have the option to share your history with us and improve our research.

Feel free to review your raw data and add more keywords! If you wish to add more keywords, just edit the keyword box and re-upload your data.

If you did not upload your file in the "Home" page, nothing will be sent to us.
""")

st.button("Send your Data")