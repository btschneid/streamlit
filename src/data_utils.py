import pandas as pd
import yfinance as yf
from src.constants import DEFAULT_TICKERS_LIST, DEFAULT_START_DATE, DEFAULT_END_DATE, DATA_FOLDER_PATH

def get_last_market_day(end_date):
    """Get the last market day before or on the given date"""
    # Convert to datetime and subtract one day to start checking
    check_date = pd.to_datetime(end_date).tz_localize('UTC') - pd.Timedelta(days=1)
    
    # Try up to 5 days back (to account for weekends and holidays)
    for _ in range(5):
        # Check if this date exists in any of our default tickers' data
        for ticker in DEFAULT_TICKERS_LIST:
            try:
                df = pd.read_csv(f'{DATA_FOLDER_PATH}/{ticker}.csv')
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
            df = pd.read_csv(f'{DATA_FOLDER_PATH}/{ticker}.csv')
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
        df.to_csv(f'{DATA_FOLDER_PATH}/{ticker}.csv')
        return True
    except Exception as e:
        print(f"Error downloading data for {ticker}: {str(e)}")
        return False

def check_and_download_default_data():
    """Check and download data for default tickers if not already present"""
    for ticker in DEFAULT_TICKERS_LIST:
        download_stock_data(ticker, DEFAULT_START_DATE, DEFAULT_END_DATE)

def download_pair_data(ticker1, ticker2, start_date, end_date):
    """Download and process data for a pair of tickers"""
    # Download data for both tickers if needed
    download_stock_data(ticker1, start_date, end_date)
    download_stock_data(ticker2, start_date, end_date)
    
    # Download data for both tickers
    df1 = pd.read_csv(f'{DATA_FOLDER_PATH}/{ticker1}.csv')
    df2 = pd.read_csv(f'{DATA_FOLDER_PATH}/{ticker2}.csv')
    
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

def is_valid_ticker(ticker):
    """Check if ticker exists on Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker)
        # Try to get info, if it fails the ticker doesn't exist
        info = stock.info
        return True
    except:
        return False 