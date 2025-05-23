import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import yfinance as yf
import time

PRIMARY_COLOR = "#ff4b4b"
SELECTED_PRIMARY_COLOR = "#b83232"

DEFAULT_TICKERS_LIST = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA"]
TICKERS_SELECTION_COLORS = {ticker: PRIMARY_COLOR for ticker in DEFAULT_TICKERS_LIST}

DEFAULT_START_DATE = "2016-01-04"
DEFAULT_END_DATE = datetime.today().strftime("%Y-%m-%d")

# Set page config to use full width
st.set_page_config(layout="wide")

# Initialize session state for selected ticker if not exists
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "default"

# Initialize session state for ticker list
if "ticker_list" not in st.session_state:
    st.session_state.ticker_list = DEFAULT_TICKERS_LIST  # Default tickers

if "ticker_color_map" not in st.session_state:
    st.session_state.ticker_color_map = TICKERS_SELECTION_COLORS

# Initialize a flag to clear input
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

if "ticker_pair" not in st.session_state:
    st.session_state.ticker_pair = ["", ""]

if "pair_data" not in st.session_state:
    # Initialize with empty dataframe with correct columns
    st.session_state.pair_data = pd.DataFrame(columns=['date', 'adj_close_TICKER1', 'vol_TICKER1', 'adj_close_TICKER2', 'vol_TICKER2'])

if "start_date" not in st.session_state:
    st.session_state.start_date = DEFAULT_START_DATE

if "end_date" not in st.session_state:
    st.session_state.end_date = DEFAULT_END_DATE

if 'show_error' not in st.session_state:
    st.session_state.show_error = False

if 'error_message' not in st.session_state:
    st.session_state.error_message = "⚠️ ERROR ⚠️"

def get_last_market_day(end_date):
    """Get the last market day before or on the given date"""
    # Convert to datetime and subtract one day to start checking
    check_date = pd.to_datetime(end_date).tz_localize('UTC') - pd.Timedelta(days=1)
    
    # Try up to 5 days back (to account for weekends and holidays)
    for _ in range(5):
        # Check if this date exists in any of our default tickers' data
        for ticker in DEFAULT_TICKERS_LIST:
            try:
                df = pd.read_csv(f'{ticker}.csv')
                df['date'] = pd.to_datetime(df['date'], utc=True)
                if check_date.date() in df['date'].dt.date.values:
                    return check_date.date()
            except (FileNotFoundError, KeyError, ValueError):
                continue
        # If not found, go back one more day
        check_date = check_date - pd.Timedelta(days=1)
    
    # If we can't find a market day, return the original end date minus 1 day
    return (pd.to_datetime(end_date).tz_localize('UTC') - pd.Timedelta(days=1)).date()

def download_stock_data(ticker, start_date, end_date):
    """Download stock data from Yahoo Finance and save to CSV"""
    try:
        # First check if we already have the data
        try:
            df = pd.read_csv(f'{ticker}.csv')
            df['date'] = pd.to_datetime(df['date'], utc=True)
            
            # Convert input dates to UTC and get just the date part
            start_timestamp = pd.to_datetime(start_date).tz_localize('UTC').date()
            end_timestamp = get_last_market_day(end_date)
            
            # Get just the date part from the dataframe
            df_dates = df['date'].dt.date
            
            # Check if we have data covering the requested range
            if df_dates.min() <= start_timestamp and df_dates.max() >= end_timestamp:
                return True  # We already have the data we need
        except (FileNotFoundError, KeyError, ValueError):
            pass  # If any error occurs, we'll download fresh data
        
        # If we don't have the data, download it
        stock = yf.Ticker(ticker)

        # Download historical data
        hist_data = stock.history(start=start_date, end=end_date, auto_adjust=False)

        # Select and rename columns to follow financial industry conventions
        df = hist_data[['Adj Close', 'Volume']].copy()
        df.columns = ['adj_close', 'vol']
        df.index.name = 'date'
        
        # Save to CSV
        df.to_csv(f'{ticker}.csv')
        return True
    except Exception as e:
        st.error(f"Error downloading data for {ticker}: {str(e)}")
        return False

def check_and_download_default_data():
    """Check and download data for default tickers if not already present"""
    for ticker in DEFAULT_TICKERS_LIST:
        download_stock_data(ticker, DEFAULT_START_DATE, DEFAULT_END_DATE)

def download_pair_data(ticker1, ticker2, start_date, end_date):
    # Download data for both tickers if needed
    download_stock_data(ticker1, start_date, end_date)
    download_stock_data(ticker2, start_date, end_date)
    
    # Download data for both tickers
    df1 = pd.read_csv(f'{ticker1}.csv')
    df2 = pd.read_csv(f'{ticker2}.csv')
    
    # Convert dates to datetime with UTC
    df1['date'] = pd.to_datetime(df1['date'], utc=True)
    df2['date'] = pd.to_datetime(df2['date'], utc=True)
    
    # Filter by date range
    start_timestamp = pd.Timestamp(start_date).tz_localize('UTC')
    end_timestamp = pd.Timestamp(end_date).tz_localize('UTC')
    
    mask1 = (df1['date'] >= start_timestamp) & (df1['date'] <= end_timestamp)
    mask2 = (df2['date'] >= start_timestamp) & (df2['date'] <= end_timestamp)
    
    df1 = df1.loc[mask1]
    df2 = df2.loc[mask2]
    
    # Add ticker suffix to columns
    df1 = df1.add_suffix(f'_{ticker1}')
    df2 = df2.add_suffix(f'_{ticker2}')
    
    # Merge the dataframes on date
    df1 = df1.rename(columns={f'date_{ticker1}': 'date'})
    df2 = df2.rename(columns={f'date_{ticker2}': 'date'})
    
    merged_df = pd.merge(df1, df2, on='date', how='inner')
    
    return merged_df

def create_plot():
    # If we have pair data, show both tickers
    if hasattr(st.session_state, 'pair_data') and not st.session_state.pair_data.empty:
        ticker1 = st.session_state.ticker_pair[0]
        ticker2 = st.session_state.ticker_pair[1]
        
        # Create a line graph using Plotly with both tickers
        fig = go.Figure()
        
        # Add first ticker
        fig.add_trace(go.Scatter(
            x=st.session_state.pair_data['date'],
            y=st.session_state.pair_data[f'adj_close_{ticker1}'],
            mode='lines',
            name=f'{ticker1}',
            line=dict(color='#2ecc71', width=2)
        ))
        
        # Add second ticker
        fig.add_trace(go.Scatter(
            x=st.session_state.pair_data['date'],
            y=st.session_state.pair_data[f'adj_close_{ticker2}'],
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
    
    # If no pair data, show first default ticker
    ticker = DEFAULT_TICKERS_LIST[0]
    
    # Download data if needed
    download_stock_data(ticker, st.session_state.start_date, st.session_state.end_date)
    
    df = pd.read_csv(f'{ticker}.csv')
    
    # Convert date column to datetime with UTC
    df['date'] = pd.to_datetime(df['date'], utc=True)
    
    # Filter data based on selected date range
    start_timestamp = pd.Timestamp(st.session_state.start_date).tz_localize('UTC')
    end_timestamp = pd.Timestamp(st.session_state.end_date).tz_localize('UTC')
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

def update_ticker(ticker):
    st.session_state.selected_ticker = ticker

def is_valid_ticker(ticker):
    """Check if ticker exists on Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        # Try to get info, if it fails the ticker doesn't exist
        info = stock.info
        return True
    except:
        return False

# Check and download default ticker data on launch
check_and_download_default_data()

# Top Row

col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 3, 0.7, 1.6, 0.7])

with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d"),
        min_value=datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d"),
        max_value=datetime.today()
    )

    st.session_state.start_date = start_date

with col2:
    # Calculate default end date value
    default_end = datetime.strptime(DEFAULT_END_DATE, "%Y-%m-%d").date()
    if default_end < st.session_state.start_date:
        default_end = st.session_state.start_date + timedelta(days=1)

    end_date = st.date_input(
        "End Date",
        value=default_end,
        min_value=st.session_state.start_date + timedelta(days=1),
        max_value=datetime.today().date()
    )

    st.session_state.end_date = end_date

# ==============================================================================

# Top-level layout

st.markdown("""
<style>
div.stButton > button:first-child {
    width: 70%;
    margin: 0 auto;
    display: block;
}
</style>
""", unsafe_allow_html=True)

# Title
with col4:
    st.markdown("<div style='text-align: center;'><h1>Risk Engine Simulator</h1></div>", unsafe_allow_html=True)

# Run Button
with col6:
    st.markdown("""
        <style>
        div[data-testid="stButton"] {
            display: flex;
            align-items: center;
            height: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    if st.button("Run Statistical Arbitrage", key="run", type="primary"):
        if (st.session_state.ticker_pair[0] == ""):
            st.session_state.error_message = "⚠️ To continue, please click the **'Find Best Cointegrated Pair'** button to select two tickers ⚠️"
            st.session_state.show_error = True

# ==============================================================================

# Main content area
col1, col2 = st.columns([2, 1])

# Display the plot

with col1:
    st.plotly_chart(create_plot(), use_container_width=True)

# Ticker List

with col2:
    # Input field for new ticker
    col_input, col_add = st.columns([3, 1])
    
    with col_input:
        # Clear input if flag is set
        input_value = "" if st.session_state.clear_input else st.session_state.get("ticker_input", "")
        if st.session_state.clear_input:
            st.session_state.clear_input = False
            
        new_ticker = st.text_input(
            "Add Ticker", 
            value=input_value,
            placeholder="Enter ticker symbol...",
            label_visibility="collapsed",
            key="ticker_input"
        )
    
    with col_add:
        if st.button("Add", key="add_ticker_btn", type="secondary"):
            if new_ticker:
                if new_ticker.upper() not in st.session_state.ticker_list:
                    if is_valid_ticker(new_ticker.upper()):
                        st.session_state.ticker_list.append(new_ticker.upper())
                        st.session_state.ticker_color_map[new_ticker.upper()] = PRIMARY_COLOR
                        st.session_state.clear_input = True  # Set flag to clear input
                        st.rerun()
                    else:
                        st.session_state.error_message = f"⚠️ Ticker '{new_ticker.upper()}' does not exist on Yahoo Finance ⚠️"
                        st.session_state.show_error = True
                        st.rerun()

    
    # Use Streamlit's built-in container with height parameter
    ticker_container = st.container(height=355)
    
    with ticker_container:
        # Display ticker buttons inside the scrollable container
        for ticker in st.session_state.ticker_list:
            col_btn, col_remove = st.columns([5, 1])
            
            with col_btn:
                st.markdown(f"""
                    <div style="
                        background-color: {st.session_state.ticker_color_map[ticker]};
                        color: white;
                        padding: 0.5rem 1rem;
                        border-radius: 0.5rem;
                        text-align: center;
                        font-weight: 600;
                        border: none;
                        width: 100%;
                        box-sizing: border-box;
                        margin: 0.25rem 0;
                    ">
                        {ticker}
                    </div>
                """, unsafe_allow_html=True)
            
            with col_remove:
                if st.button("×", key=f"remove_{ticker}", help=f"Remove {ticker}"):
                    st.session_state.ticker_list.remove(ticker)
                    st.session_state.ticker_color_map.pop(ticker, None)
                    st.rerun()

    if st.button("Find Best Cointegrated Pair", key="Test", type="secondary"):
        if len(st.session_state.ticker_list) >= 2:
            # Get two random different indices
            indices = random.sample(range(len(st.session_state.ticker_list)), 2)
            ticker1 = st.session_state.ticker_list[indices[0]]
            ticker2 = st.session_state.ticker_list[indices[1]]

            if st.session_state.ticker_pair[0] != "":
                st.session_state.ticker_color_map[st.session_state.ticker_pair[0]] = PRIMARY_COLOR
                st.session_state.ticker_color_map[st.session_state.ticker_pair[1]] = PRIMARY_COLOR
            
            st.session_state.ticker_pair[0] = ticker1
            st.session_state.ticker_pair[1] = ticker2
            
            st.session_state.ticker_color_map[ticker1] = SELECTED_PRIMARY_COLOR
            st.session_state.ticker_color_map[ticker2] = SELECTED_PRIMARY_COLOR

            # Download and process the pair data
            pair_data = download_pair_data(
                ticker1, 
                ticker2, 
                st.session_state.start_date, 
                st.session_state.end_date
            )
            
            # Store the pair data in session state
            st.session_state.pair_data = pair_data

            st.rerun()

# ==============================================================================

# Bottom Section
col1, col2 = st.columns([2, 1])

# Statistics section
with col1:
    pass
    #st.markdown("<div style='text-align: center;'><h3>Statistics</h3></div>", unsafe_allow_html=True)
    # Add your statistics content here

with col2:
    if st.session_state.show_error:
        st.markdown("""
            <style>
            div[data-testid="stAlert"] {
                text-align: center;
            }
            </style>
        """, unsafe_allow_html=True)
        error_container = st.empty()
        error_container.error(f"{st.session_state.error_message}")

        time.sleep(0.15)
        
        # Create a dismiss button
        if st.button("Dismiss"):
            st.session_state.show_error = False
            st.rerun()
        
        # Auto-dismiss after 5 seconds
        time.sleep(5)
        if st.session_state.show_error:  # Only dismiss if it hasn't been manually dismissed
            st.session_state.show_error = False
            st.rerun()
