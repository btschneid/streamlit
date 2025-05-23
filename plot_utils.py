import plotly.graph_objects as go
from data_utils import download_stock_data
import pandas as pd
from constants import DATA_FOLDER_PATH

def create_pair_plot(pair_data, ticker1, ticker2):
    """Create a plot for a pair of stocks"""
    fig = go.Figure()
    
    # Add first ticker
    fig.add_trace(go.Scatter(
        x=pair_data['date'],
        y=pair_data[f'adj_close_{ticker1}'],
        mode='lines',
        name=f'{ticker1}',
        line=dict(color='#2ecc71', width=2)
    ))
    
    # Add second ticker
    fig.add_trace(go.Scatter(
        x=pair_data['date'],
        y=pair_data[f'adj_close_{ticker2}'],
        mode='lines',
        name=f'{ticker2}',
        line=dict(color='#e74c3c', width=2)
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        showlegend=True,
        xaxis_title="Date",
        yaxis_title="Adj Close ($)",
        legend=dict(
            x=0.07,
            y=1,
            xanchor='right',
            yanchor='bottom'
        )
    )
    
    return fig

def create_single_plot(ticker, start_date, end_date):
    """Create a plot for a single stock"""
    # Download data if needed
    download_stock_data(ticker, start_date, end_date)
    
    # Read the data
    df = pd.read_csv(f'{DATA_FOLDER_PATH}/{ticker}.csv')
    df['date'] = pd.to_datetime(df['date'], utc=True)
    
    # Filter data based on selected date range
    start_timestamp = pd.Timestamp(start_date).tz_localize('UTC')
    end_timestamp = pd.Timestamp(end_date).tz_localize('UTC')
    mask = (df['date'] >= start_timestamp) & (df['date'] <= end_timestamp)
    df = df.loc[mask]
    
    # Create a line graph using Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['adj_close'],
        mode='lines',
        name=f'{ticker}',
        line=dict(color='#2ecc71', width=2)
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        showlegend=True,
        xaxis_title="Date",
        yaxis_title="Adj Close ($)",
        legend=dict(
            x=0.07,
            y=1,
            xanchor='right',
            yanchor='bottom'
        )
    )
    
    return fig 