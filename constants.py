import datetime

# Colors
PRIMARY_COLOR = "#ff4b4b"
SELECTED_PRIMARY_COLOR = "#b83232"

# Default tickers
DEFAULT_TICKERS_LIST = ["AAPL", "MSFT", "GOOG", "NVDA", "TSLA", "AMZN"]
TICKERS_SELECTION_COLORS = {ticker: PRIMARY_COLOR for ticker in DEFAULT_TICKERS_LIST}

# Default dates
DEFAULT_START_DATE = "2016-01-04"
DEFAULT_END_DATE = datetime.datetime.today().strftime("%Y-%m-%d") 

# Paths
DATA_FOLDER_PATH = "data"