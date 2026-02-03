## Browsing History 

This app analyzes your Google Chrome browsing history. It does not save any of your data.

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

This project was greatly inspired by [the Cookies Project](https://cookiesproject.streamlit.app/) made by Jessica, Nina, Crystal, and Dianna from Wellesley Cred Lab.
