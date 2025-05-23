import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
from datetime import datetime, timedelta

from constants import (
    PRIMARY_COLOR, SELECTED_PRIMARY_COLOR, DEFAULT_TICKERS_LIST,
    TICKERS_SELECTION_COLORS, DEFAULT_START_DATE, DEFAULT_END_DATE, DATA_FOLDER_PATH
)
from data_utils import (
    check_and_download_default_data, download_pair_data,
    is_valid_ticker
)
from stats_utils import calculate_pair_statistics
from plot_utils import create_pair_plot, create_single_plot

# Set page config to use full width
st.set_page_config(layout="wide")

# Initialize session state variables
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "default"

if "ticker_list" not in st.session_state:
    st.session_state.ticker_list = DEFAULT_TICKERS_LIST

if "ticker_color_map" not in st.session_state:
    st.session_state.ticker_color_map = TICKERS_SELECTION_COLORS

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

if "ticker_pair" not in st.session_state:
    st.session_state.ticker_pair = ["", ""]

if "pair_data" not in st.session_state:
    st.session_state.pair_data = pd.DataFrame(columns=['date', 'adj_close_TICKER1', 'vol_TICKER1', 'adj_close_TICKER2', 'vol_TICKER2'])

if "start_date" not in st.session_state:
    st.session_state.start_date = DEFAULT_START_DATE

if "end_date" not in st.session_state:
    st.session_state.end_date = DEFAULT_END_DATE

if 'show_error' not in st.session_state:
    st.session_state.show_error = False

if 'error_message' not in st.session_state:
    st.session_state.error_message = "⚠️ ERROR ⚠️"

if 'last_start_date' not in st.session_state:
    st.session_state.last_start_date = DEFAULT_START_DATE

if 'last_end_date' not in st.session_state:
    st.session_state.last_end_date = DEFAULT_END_DATE

if 'should_update_stats' not in st.session_state:
    st.session_state.should_update_stats = False

if 'input_counter' not in st.session_state:
    st.session_state.input_counter = 0

# Custom CSS
st.markdown("""
<style>
div.stButton > button:first-child {
    width: 70%;
    margin: 0 auto;
    display: block;
}
</style>
""", unsafe_allow_html=True)

# Check and download default ticker data on launch
check_and_download_default_data()

# Top Row
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 3, 0.2, 2.6, 0.2])

# Dates
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d"),
        min_value=datetime.strptime(DEFAULT_START_DATE, "%Y-%m-%d"),
        max_value=datetime.today()
    )

    if start_date != st.session_state.last_start_date:
        st.session_state.state_date = start_date
        st.session_state.last_start_date = start_date
        if st.session_state.ticker_pair[0] != "" and st.session_state.ticker_pair[1] != "":
            pair_data = download_pair_data(
                st.session_state.ticker_pair[0],
                st.session_state.ticker_pair[1],
                start_date,
                st.session_state.end_date
            )
            st.session_state.pair_data = pair_data
        st.session_state.should_update_stats = True
    st.session_state.start_date = start_date

with col2:
    default_end = datetime.strptime(DEFAULT_END_DATE, "%Y-%m-%d").date()
    if default_end < st.session_state.start_date:
        default_end = st.session_state.start_date + timedelta(days=1)

    end_date = st.date_input(
        "End Date",
        value=default_end,
        min_value=st.session_state.start_date + timedelta(days=1),
        max_value=datetime.today().date()
    )

    if end_date != st.session_state.last_end_date:
        st.session_state.end_date = end_date
        st.session_state.last_end_date = end_date
        if st.session_state.ticker_pair[0] != "" and st.session_state.ticker_pair[1] != "":
            pair_data = download_pair_data(
                st.session_state.ticker_pair[0],
                st.session_state.ticker_pair[1],
                st.session_state.start_date,
                end_date
            )
            st.session_state.pair_data = pair_data
        st.session_state.should_update_stats = True
    st.session_state.end_date = end_date

# Title
with col4:
    st.markdown("<div style='text-align: center;'><h1>Risk Engine Simulator</h1></div>", unsafe_allow_html=True)

# Run Button
with col6:
    if st.button("Find Best Cointegrated Pair", key="Test", type="secondary"):
        if len(st.session_state.ticker_list) >= 2:
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

            pair_data = download_pair_data(
                ticker1, 
                ticker2, 
                st.session_state.start_date, 
                st.session_state.end_date
            )
            
            st.session_state.pair_data = pair_data
            st.session_state.should_update_stats = True

            st.rerun()
    
    if st.session_state.show_error:
        col1, col2, col3 = st.columns([1, 6, 1])
        with col2:
            st.markdown(f"""
                <div style="
                    background-color: #fee;
                    border: 1px solid #fcc;
                    border-radius: 0.25rem;
                    padding: 0.375rem 0.75rem;
                    color: #c53030;
                    font-size: 0.875rem;
                    text-align: center;
                    height: 38px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                ">
                    {st.session_state.error_message}
                </div>
            """, unsafe_allow_html=True)

# Main content area
col1, col2 = st.columns([2, 1])

# Plot
with col1:
    if hasattr(st.session_state, 'pair_data') and not st.session_state.pair_data.empty:
        st.plotly_chart(create_pair_plot(
            st.session_state.pair_data,
            st.session_state.ticker_pair[0],
            st.session_state.ticker_pair[1]
        ), use_container_width=True)
    else:
        st.plotly_chart(create_single_plot(
            DEFAULT_TICKERS_LIST[0],
            st.session_state.start_date,
            st.session_state.end_date
        ), use_container_width=True)

with col2:
    # Input field for new ticker
    col_input, col_add = st.columns([3, 1])
    
    with col_input:
        new_ticker = st.text_input(
            "Add Ticker", 
            placeholder="Enter ticker symbol...",
            label_visibility="collapsed",
            key=f"ticker_input_{st.session_state.input_counter}"
        )
    
    with col_add:
        if st.button("Add", key="add_ticker_btn", type="secondary"):
            if new_ticker:
                if new_ticker.upper() not in st.session_state.ticker_list:
                    if is_valid_ticker(new_ticker.upper()):
                        st.session_state.ticker_list.append(new_ticker.upper())
                        st.session_state.ticker_color_map[new_ticker.upper()] = PRIMARY_COLOR
                        st.session_state.input_counter += 1
                        st.session_state.show_error = False
                        st.rerun()
                    else:
                        st.session_state.error_message = f"⚠️ Ticker '{new_ticker.upper()}' does not exist on Yahoo Finance ⚠️"
                        st.session_state.show_error = True
                        st.rerun()
                else:
                    st.session_state.error_message = f"⚠️ Ticker '{new_ticker.upper()}' is already in the list ⚠️"
                    st.session_state.show_error = True
                    st.rerun()

    ticker_container = st.container(height=355)
    
    with ticker_container:
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

# Bottom Section
col1, col2 = st.columns([100, 0.001])

# Statistics section
with col1:
    # Create 3 rows of statistics
    for row in range(3):
        cols = st.columns(6)
        for col in range(6):
            with cols[col]:
                if hasattr(st.session_state, 'pair_data') and not st.session_state.pair_data.empty and st.session_state.should_update_stats:
                    stats = calculate_pair_statistics(
                        st.session_state.pair_data,
                        st.session_state.ticker_pair[0],
                        st.session_state.ticker_pair[1]
                    )
                    
                    if row == 0:
                        if col == 0:
                            st.metric("Cumulative Return", f"{stats['cum_return']:.2f}%", 
                                    help="Total return over the entire period, expressed as a percentage")
                        elif col == 1:
                            st.metric("Annualized Return", f"{stats['annual_return']:.2f}%",
                                    help="Average yearly return, annualized from the total period")
                        elif col == 2:
                            st.metric("Sharpe Ratio", f"{stats['sharpe']:.2f}",
                                    help="Risk-adjusted return measure. Higher values indicate better risk-adjusted performance")
                        elif col == 3:
                            st.metric("Sortino Ratio", f"{stats['sortino']:.2f}",
                                    help="Risk-adjusted return measure that only considers downside volatility")
                        elif col == 4:
                            st.metric("Calmar Ratio", f"{stats['calmar']:.2f}",
                                    help="Annualized return divided by maximum drawdown. Higher values indicate better risk-adjusted returns")
                        else:
                            st.metric("Max Drawdown", f"{stats['max_drawdown']:.2f}%",
                                    help="Largest percentage drop from a peak to a subsequent trough")
                    elif row == 1:
                        if col == 0:
                            st.metric("VaR (95%)", f"{stats['var_95']:.2f}%",
                                    help="Value at Risk at 95% confidence level - maximum expected loss over a given time period")
                        elif col == 1:
                            st.metric("CVaR (95%)", f"{stats['cvar_95']:.2f}%",
                                    help="Conditional Value at Risk - average of losses beyond the VaR threshold")
                        elif col == 2:
                            st.metric("Profit Factor", f"{stats['profit_factor']:.2f}",
                                    help="Ratio of gross profits to gross losses. Values > 1 indicate profitable trading")
                        elif col == 3:
                            st.metric("MAE", f"{stats['mae']:.2f}%",
                                    help="Maximum Adverse Excursion - largest percentage drop from entry to lowest point")
                        elif col == 4:
                            st.metric("ADF Statistic", f"{stats['adf_stat']:.4f}",
                                    help="Augmented Dickey-Fuller test statistic for testing stationarity of the spread")
                        else:
                            st.metric("P-value", f"{stats['p_value']:.4f}",
                                    help="P-value from ADF test. Lower values suggest stronger evidence of mean reversion")
                    else:
                        if col == 0:
                            st.metric("Hedge Ratio", f"{stats['beta']:.4f}",
                                    help="Optimal ratio of the two assets for hedging, calculated using OLS regression")
                        elif col == 1:
                            st.metric("Half-life (days)", f"{stats['half_life']:.1f}" if not pd.isna(stats['half_life']) else "N/A",
                                    help="Expected time for the spread to revert half way back to its mean")
                        elif col == 2:
                            st.metric("# of Trades", f"{stats['mean_crossings']}",
                                    help="Number of times the spread crosses its mean, indicating potential trading opportunities")
                        elif col == 3:
                            st.metric("Win Rate", f"{stats['win_rate']:.1f}%",
                                    help="Percentage of profitable trades")
                        elif col == 4:
                            st.metric("Mean Duration", f"{stats['trade_duration']:.1f} days",
                                    help="Average holding period for trades")
                        else:
                            st.metric("Z-score", f"{stats['current_z']:.2f}",
                                    help="Current spread's deviation from mean in standard deviations")
                else:
                    if row == 0:
                        if col == 0:
                            st.metric("Cumulative Return", "N/A",
                                    help="Total return over the entire period, expressed as a percentage")
                        elif col == 1:
                            st.metric("Annualized Return", "N/A",
                                    help="Average yearly return, annualized from the total period")
                        elif col == 2:
                            st.metric("Sharpe Ratio", "N/A",
                                    help="Risk-adjusted return measure. Higher values indicate better risk-adjusted performance")
                        elif col == 3:
                            st.metric("Sortino Ratio", "N/A",
                                    help="Risk-adjusted return measure that only considers downside volatility")
                        elif col == 4:
                            st.metric("Calmar Ratio", "N/A",
                                    help="Annualized return divided by maximum drawdown. Higher values indicate better risk-adjusted returns")
                        else:
                            st.metric("Max Drawdown", "N/A",
                                    help="Largest percentage drop from a peak to a subsequent trough")
                    elif row == 1:
                        if col == 0:
                            st.metric("VaR (95%)", "N/A",
                                    help="Value at Risk at 95% confidence level - maximum expected loss over a given time period")
                        elif col == 1:
                            st.metric("CVaR (95%)", "N/A",
                                    help="Conditional Value at Risk - average of losses beyond the VaR threshold")
                        elif col == 2:
                            st.metric("Profit Factor", "N/A",
                                    help="Ratio of gross profits to gross losses. Values > 1 indicate profitable trading")
                        elif col == 3:
                            st.metric("MAE", "N/A",
                                    help="Maximum Adverse Excursion - largest percentage drop from entry to lowest point")
                        elif col == 4:
                            st.metric("ADF Statistic", "N/A",
                                    help="Augmented Dickey-Fuller test statistic for testing stationarity of the spread")
                        else:
                            st.metric("P-value", "N/A",
                                    help="P-value from ADF test. Lower values suggest stronger evidence of mean reversion")
                    else:
                        if col == 0:
                            st.metric("Hedge Ratio", "N/A",
                                    help="Optimal ratio of the two assets for hedging, calculated using OLS regression")
                        elif col == 1:
                            st.metric("Half-life (days)", "N/A",
                                    help="Expected time for the spread to revert half way back to its mean")
                        elif col == 2:
                            st.metric("# of Trades", "N/A",
                                    help="Number of times the spread crosses its mean, indicating potential trading opportunities")
                        elif col == 3:
                            st.metric("Win Rate", "N/A",
                                    help="Percentage of profitable trades")
                        elif col == 4:
                            st.metric("Mean Duration", "N/A",
                                    help="Average holding period for trades")
                        else:
                            st.metric("Z-score", "N/A",
                                    help="Current spread's deviation from mean in standard deviations")

    # Reset the update flag after displaying statistics
    st.session_state.should_update_stats = False 