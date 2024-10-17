import streamlit as st
from predictors import prediction_form
from page_template import header, footer
from sentiment_analyzer import sentiment_analyzer_form
from PIL import Image
# Set the page configuration
st.set_page_config(page_title="Product Insights", page_icon=":mag:", layout="centered")

# Load CSS styles
with open('static/css/styles.css') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'Home'  # Default to Home

# Initialize session state for processing
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Function to disable navigation buttons
def navigation_disabled():
    return st.session_state.processing

# Display the header
header()

# Disable navigation while processing
with st.sidebar:
    page = st.radio("Navigation", ["Home", "Sentiment Analyzer", "Price Predictor", "Demand Predictor"], disabled=navigation_disabled())

# Update the session state based on navigation immediately
st.session_state.page = page

# Conditional rendering based on the selected page
if st.session_state.page == "Home":
    st.write("## Welcome to Product Insights!")
    st.write("Use the navigation menu to switch between different tools.")
elif st.session_state.page == "Sentiment Analyzer":
    sentiment_analyzer_form()
elif st.session_state.page == "Price Predictor":
    prediction_form("Price")
elif st.session_state.page == "Demand Predictor":
    prediction_form("Demand")

# Display the footer
footer()
