import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

def calculate_pair_statistics(pair_data, ticker1, ticker2):
    """Calculate all statistics for a pair of stocks"""
    # Calculate returns and spreads
    returns1 = pair_data[f'adj_close_{ticker1}'].pct_change()
    returns2 = pair_data[f'adj_close_{ticker2}'].pct_change()
    spread = pair_data[f'adj_close_{ticker1}'] - pair_data[f'adj_close_{ticker2}']
    
    # Calculate hedge ratio (beta) using OLS regression
    X = sm.add_constant(pair_data[f'adj_close_{ticker2}'])
    y = pair_data[f'adj_close_{ticker1}']
    model = sm.OLS(y, X).fit()
    beta = model.params.iloc[1]  # Get the second parameter (beta)
    
    # Calculate ADF test statistics
    adf_result = adfuller(spread.dropna())
    adf_stat = adf_result[0]
    p_value = adf_result[1]
    
    # Calculate half-life of mean reversion
    spread_lag = spread.shift(1)
    spread_ret = spread - spread_lag
    spread_lag = spread_lag.dropna()
    spread_ret = spread_ret.dropna()
    half_life_model = sm.OLS(spread_ret, sm.add_constant(spread_lag)).fit()
    half_life = -np.log(2) / half_life_model.params.iloc[1] if half_life_model.params.iloc[1] < 0 else np.nan
    
    # Calculate z-score
    z_score = (spread - spread.mean()) / spread.std()
    current_z = z_score.iloc[-1]
    
    # Calculate number of trades (crossings of mean)
    mean_crossings = np.sum(np.diff(np.signbit(spread - spread.mean())))
    
    # Calculate performance metrics
    cum_return = (pair_data[f'adj_close_{ticker1}'].iloc[-1] / 
               pair_data[f'adj_close_{ticker1}'].iloc[0] - 1) * 100
    annual_return = ((1 + cum_return/100) ** (252/len(pair_data)) - 1) * 100
    vol = returns1.std() * np.sqrt(252) * 100
    sharpe = annual_return / vol if vol != 0 else 0
    
    # Calculate Sortino Ratio (using negative returns only)
    neg_returns = returns1[returns1 < 0]
    downside_vol = neg_returns.std() * np.sqrt(252) * 100
    sortino = annual_return / downside_vol if downside_vol != 0 else 0
    
    # Calculate Calmar Ratio
    max_drawdown = ((pair_data[f'adj_close_{ticker1}'] / 
                  pair_data[f'adj_close_{ticker1}'].expanding().max() - 1) * 100).min()
    calmar = abs(annual_return / max_drawdown) if max_drawdown != 0 else 0
    
    # Calculate VaR and CVaR
    var_95 = np.percentile(returns1, 5) * 100
    cvar_95 = returns1[returns1 <= np.percentile(returns1, 5)].mean() * 100
    
    # Calculate Profit Factor
    gross_profit = returns1[returns1 > 0].sum()
    gross_loss = abs(returns1[returns1 < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
    
    # Calculate MAE
    rolling_max = pair_data[f'adj_close_{ticker1}'].expanding().max()
    mae = ((pair_data[f'adj_close_{ticker1}'] - rolling_max) / rolling_max * 100).min()
    
    # Calculate Win Rate
    win_rate = (returns1 > 0).mean() * 100
    
    # Calculate Mean Trade Duration
    trade_duration = len(pair_data) / mean_crossings if mean_crossings > 0 else 0
    
    return {
        'cum_return': cum_return,
        'annual_return': annual_return,
        'sharpe': sharpe,
        'sortino': sortino,
        'calmar': calmar,
        'max_drawdown': max_drawdown,
        'var_95': var_95,
        'cvar_95': cvar_95,
        'profit_factor': profit_factor,
        'mae': mae,
        'adf_stat': adf_stat,
        'p_value': p_value,
        'beta': beta,
        'half_life': half_life,
        'mean_crossings': mean_crossings,
        'win_rate': win_rate,
        'trade_duration': trade_duration,
        'current_z': current_z
    } 