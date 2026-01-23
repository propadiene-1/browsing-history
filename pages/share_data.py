import streamlit as st

st.markdown("""
### Share your data (OPTIONAL)
This part is completely optional. If you found the app helpful, you have the option to share your history with us and improve our research.
""")

st.markdown("""
#### Step 1: Exclude domains
If you choose to help us out by sharing your data, you can list any number of domains in this box to exclude. We will not save these domains anywhere.
You can also list any number of keywords-- any domain, search, or url which contains the keyword will also be removed.
""")

st.markdown("""
#### Step 2: Review your data
Upload your file below to apply the automatic filters and view the data that will be shared with the team. Please review it to make sure you have excluded everything that you would not want to share.

**Note: The data below will not be sent to our database.** The table is only for you to view on your local website. Only hitting "send" in Step 3 will send it to us.
""")

def file_upload():
  uploaded_file = st.file_uploader(
    "placeholder label to avoid error",
    label_visibility="collapsed",
    type=None,
  )
  if uploaded_file is None:
    st.warning("Please upload the file to proceed.")
    return
  return

def filter_data(df, keywords): #keywords will be stored as a dic
  for index, row in df.iterrows():
    for keyword in keywords.keys():
      if row.str.contains(keyword):
        df.drop(index=index)
  return df

file_upload()

st.markdown("""
#### Step 3: Upload your data
If you are comfortable with the data being shared, go ahead and hit 'send' to send it to our database below. If you want to go back and exclude more domains, you can always edit your list and re-upload your data above. We thank you for your contribution!
""")