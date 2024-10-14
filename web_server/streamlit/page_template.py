import streamlit as st

# Define the unified header
def header():
    st.markdown("""
        <div style="background-color: #4CAF50; padding: 10px;">
            <h1 style="color: white; text-align: center;">Pioneers Market Analyzer</h1>
        </div>
    """, unsafe_allow_html=True)

# Define the unified footer
def footer():
    st.markdown("""
        <hr>
        <div style="text-align: center; padding: 10px;">
            <p>&copy; 2024 Pioneers Market Analyzer. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)

# Define the navigation bar

def navigation():
    st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <a href="/?page=home" target="_self" style="margin-right: 15px;">Home</a>
            <a href="/?page=sentiment_analyzer" target="_self" style="margin-right: 15px;">Sentiment Analyzer</a>
            <a href="/?page=price_predictor" target="_self" style="margin-right: 15px;">Price Predictor</a>
            <a href="/?page=demand_predictor"target="_self" >Demand Predictor</a>
        </div>
        <hr>
    """, unsafe_allow_html=True)
