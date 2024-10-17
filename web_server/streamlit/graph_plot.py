import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np


def plot(data,type):
    # Create a Plotly graph
    fig = go.Figure()

    # Plot historical prices
    fig.add_trace(go.Scatter(
        x=data[data['Type'] == 'Historical']["Date"],
        y=data[data['Type'] == 'Historical']["Price"],
        mode='lines',
        name='Historical Price',
        line=dict(color='blue', width=3),
        hovertemplate='%{y:.2f}<extra></extra>'
    ))

    # Plot forecasted prices
    fig.add_trace(go.Scatter(
        x=data[data['Type'] == 'Forecast']["Date"],
        y=data[data['Type'] == 'Forecast']["Price"],
        mode='lines',
        name='Forecasted Price',
        line=dict(color='red', width=3, dash='dash'),
        hovertemplate='%{y:.2f}<extra></extra>'
    ))

    # Add shading to represent uncertainty in forecast
    fig.add_trace(go.Scatter(
        x=np.concatenate([data[data['Type'] == 'Forecast']["Date"], data[data['Type'] == 'Forecast']["Date"][::-1]]),
        y=np.concatenate([data[data['Type'] == 'Forecast']["Price"] + 5, (data[data['Type'] == 'Forecast']["Price"] - 5)[::-1]]),
        fill='toself',
        fillcolor='rgba(255, 0, 0, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False,
        name='Uncertainty'
    ))
    
    #ind to show where forcast starts
    ind = data.index[data['Type'] == 'Forecast'][0]- data.__len__()
    # Add annotations for significant points
    fig.add_annotation(
        
        x=data["Date"].iloc[ind], 
        y=data["Price"].iloc[ind], 
        text="Forecast starts here", 
        showarrow=True, 
        arrowhead=1, 
        ax=-50, 
        ay=-50,
        bgcolor="yellow"
    )

    # Layout and design improvements
    fig.update_layout(
        title=type + " Forecast",
        xaxis_title="Date",
        yaxis_title= type,
        hovermode="x unified",
        template="plotly_white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Customize axis ranges for better visual effect
    fig.update_xaxes(rangeslider_visible=True)
    if type == "Price":
        fig.update_yaxes(tickprefix="$")
    else:
        fig.update_yaxes(tickprefix="#")


    # Render Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    '''# Optional: show raw data
    if st.checkbox("Show raw data"):
        '''
    st.subheader("Raw Data")
    st.write(data)
    print(data.describe())