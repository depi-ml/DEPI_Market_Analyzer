import streamlit as st
from predictors import prediction_form
from page_template import header, footer
from sentiment_analyzer import sentiment_analyzer_form

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
    st.write("Use the navigation above to switch between different tools.")
elif st.session_state.page == "Sentiment Analyzer":
    sentiment_analyzer_form()
elif st.session_state.page == "Price Predictor":
    prediction_form("Price")
elif st.session_state.page == "Demand Predictor":
    prediction_form("Demand")

# st.markdown(f'''
#         <div style="
#             background-color: #f0f8ff;
#             border-radius: 10px;
#             padding: 20px;
#             margin: 20px 0;
#             box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
#             animation: fadeInUp 2s ease-in-out;
#             font-size: 18px;
#             color: #333;
#             font-family: Arial, sans-serif;
#             ">
#             <p style="font-size: 24px; font-weight: bold;">Wake up to a world of flavor with Lavazza Super Crema!</p>
# <p style="font-size: 18px;">Experience the rich, creamy, and strong taste of this premium espresso blend. Each cup is bursting with flavor and a generous layer of crema, making it a true delight for your senses. ☕️</p>
# <p style="font-size: 16px;">Lavazza Super Crema is perfect for those who enjoy a strong, aromatic coffee with a smooth finish. It's versatile enough to be enjoyed black or with milk, and its medium roast ensures a balanced flavor profile. ☕</p>
# <p style="font-size: 16px;">Ready to elevate your coffee experience? <a href="https://www.amazon.com/Lavazza-Coffee-Medium-Espresso-2-2-Pound/dp/B000SDKDM4/ref=sr_1_2?crid=QY4OSBXZJPVE&dib=eyJ2IjoiMSJ9.6FVGAJzyZl1hnxMuUDnLd1xunnWtp0Pi_AnRmXp4ItiAEjuqf6piEVAAlAgNDwJ0pIAeOdscHW9C3tSlvzb8Fk9eO_tq1JjGL5P6KD7J8bybq856C204tNFQJsyifkASXQ3hiQ7EnT6FtZeSAPRoISgs4g82oZqGJKg6BFPxs1qrnFxdopqtLjkxtTeKNBB6bcUVHVjVm8vayWx_7asveSqH3axUVm8tKp17cfJwDjhNTnep8Q7sUcouC3YO0Z6q2RCDBbSvnRF-mMMT7N11DwJJGvEI0QJBc-px4UZJZn4.-e3k01kVBcGpIU6EsiakeO2Is2_6XUULgArBMKMtx14&dib_tag=se&keywords=coffee&qid=1728721147&sprefix=coffee%2Caps%2C372&sr=8-2&th=1" style="color: #007bff;">Shop Lavazza Super Crema now!</a></p>
#         </div>
#         <style>
#             @keyframes fadeInUp {{
#                 0% {{
#                     opacity: 0;
#                     transform: translateY(20px);
#                 }}
#                 100% {{
#                     opacity: 1;
#                     transform: translateY(0);
#                 }}
#             }}
#         </style>
#     ''', unsafe_allow_html=True)

# Display the footer
footer()
