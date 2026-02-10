import streamlit as st
import pandas as pd

st.set_page_config(page_title="Share your Data", layout="wide")

st.markdown("## **Share your Data**")
st.markdown("""
This part is completely optional. Our lab would like to continue working with browsing history and understanding the kind of information that is stored in search browsers.
If you found the app helpful, you have the option to share your history with us and improve our research.

To share your data, download a CSV of your history using the button below, and then upload it to this Google Form:

[**Upload your data here**](https://forms.gle/kb2rbJTU8ScxuSYr8)

Please note that the form does **store your Google profile information in order to allow for uploads**. When you send us your data, it will no longer be anonymized.

To send a less personal version, you can also choose to upload your top 1000 most visited sites on the "Data Visualization" page instead.
""")

if 'raw_visit_data' not in st.session_state:
    st.info("Please upload your file to streamlit before sharing.")
    downloaded_data = pd.DataFrame().to_csv()
else:
    downloaded_data = st.session_state.raw_visit_data.to_csv(index=False).encode("utf-8")

st.download_button(     #download button (csv)
    label="Download your Data",
    data=downloaded_data,
    file_name=f"visits_csv",
)