## Browsing History 

An interactive Streamlit dashboard to analyze your browsing history!

Currently adapted to host an event for [Love Data Week](https://www.icpsr.umich.edu/sites/icpsr/about/news-events/international-love-data-week) at Wellesley College.

### Descriptions

This app allows you to view analytics for your browsing history (such as which sites you visit the most, and how you navigate Google Search results). It uses your local browsing history file and currently works for Google Chrome, Safari, and Firefox. 

We NOT store any of your data. It's stored in a cache on the site, but will clear when you do a hard refresh (Cmd/Ctrl+Shift+R). 

However, you can choose to send us your data for research purposes! If you want to do this, you can enter any number of keywords to filter out (any search containing the keyword will be removed from the data we receive). 

### Quick Start

1. **Clone the repo**
    ```
    git clone https://github.com/propadiene-1/browsing-history.git
    ```

2. **Install requirements**
    ```
    pip install -r requirements.txt
    ```
3. **Run app in streamlit**
    ```
    streamlit run app.py
    ```
4. **Follow instructions in the app for analysis**

    ![Alt text](./static/screenshot.png)

### Handling Errors
1. **Command not found: streamlit**
   
   Instead of running with Streamlit directly, try running the following:
   ```
   python -m streamlit run app.py
   ```
   
3. **Error related to "width = 'stretch'"**

   Update your Streamlit:
   ```
   pip install --upgrade streamlit
   ```

### Authors

Made by the Wellesley Cred Lab. Advised by Eni Mustafaraj.

This project was greatly inspired by [the Cookies Project](https://cookiesproject.streamlit.app/) made by Jessica, Nina, Crystal, and Dianna from the Wellesley Cred Lab.
