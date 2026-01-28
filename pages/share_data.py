import streamlit as st
from app_functions import *

st.set_page_config(page_title="Share your Data", layout="wide")

st.markdown("## **Share your Data**")
st.markdown("""
This part is completely OPTIONAL. If you found the app helpful, you have the option to share your history with us and improve our research.
""")

st.markdown("""
### Step 1: Exclude domains
If you choose to help us out by sharing your data, you can list any number of keywords in this box to exclude. Any domain, search, or url which contains the keyword will be removed. We will not save your keywords anywhere.
""")

st.info("**NOTE:** Keywords must be comma-separated.")

user_input = st.text_area(
  "placeholder label",
  max_chars=None,
  on_change=None, 
  placeholder="Enter keywords...", 
  disabled=False, 
  label_visibility="collapsed", 
  width="stretch")

if 'keywords' not in st.session_state: #save keywords into dic for this session
  st.session_state.keywords = {}

if st.button("Save keywords"): #submit button auto-saves text box
  if user_input:
    items = [line.strip() for line in user_input.split(',') if line.strip()]
    st.session_state.keywords = {i: 0 for i in items}     #store input as keywords
    st.success(f"**SAVED KEYWORDS:** {user_input}")
  else:
    st.error("Please enter keywords to save.")

st.markdown("""
### Step 2: Upload and Review
Upload your file below to apply the automatic filters and view the data that will be shared with the team. Please review it to make sure you have excluded everything that you would not want to share.
""")

st.info("""
**NOTE:** The table below is NOT sent to our database. We only store it after you hit Send in Step 3.
""")

def filter_data(df, keywords): #keywords stored as a dic
  dropped_indices = []
  for index, row in df.iterrows():
    for keyword in keywords.keys():
      if row.astype(str).str.contains(keyword, case=False).any(): #case-insensitive, column-insensitive
        dropped_indices.append(index)
        break
  return df.drop(dropped_indices) #drop once at end for efficiency

def convert_to_df(uploaded_file):
  #process file into df
  try:
    temp_path = save_uploaded_file_to_temp(uploaded_file)
    df = load_chrome_history_db(temp_path)
  except Exception as e:
    st.error(f"Unable to read the file. Error: {e}")
    return

  #data cleaning
  df = add_domain(df)
  df["visit_time"] = df["visit_time"].apply(chrome_time_to_datetime) #human-readable time
  raw_data = df                  #save raw visit data
  df = split_sessions(df)     #record sessions > visits
  df = add_session_length(df)

  return df

#FILE PROCESSING (COPIED FROM MAIN APP)
uploaded_file = st.file_uploader(   #render file uploader
  "placeholder label to avoid error",
  label_visibility="collapsed",
  type=None,
)
if uploaded_file is None:
  st.warning("Please upload the file to proceed.")

else:
  df = convert_to_df(uploaded_file) #convert to df
  df = filter_data(df, st.session_state.keywords) #filter data

  #RENDER FINAL TABLE
  st.subheader("Your Filtered Browsing Data")
  col1, col2, col3 = st.columns([0.3,0.3,0.4]) #overall stats bar
  with col1:
    st.write(f"**Total logged browsing sessions:**  {len(df)}")
  with col2:
    st.write(f"**Unique domains:** {df['domain'].nunique()}")
  with col3:
    st.write(f"**Timeframe:** {df['session_start'].min()} to {df['session_end'].max()}")

  st.info("Filters have been applied. You can search for keywords on the top right.")
  render_raw_table(df)

st.markdown("""
### Step 3: Upload your data
If you are comfortable with the data being shared, go ahead and hit 'send' to send it to our database below. If you want to go back and exclude more domains, you can always edit your list and re-upload your data above. We thank you for your contribution!
""")

st.button("Send your Data")