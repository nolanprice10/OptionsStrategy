import yfinance as yf
import pandas as pd

ticker = 'SPY'
interval = '5m'
period = '60d'

or_minutes = 15
or_bars = or_minutes // 5

stop_loss = 0.5
take_profit = 0.5
leverage = 8.0

starting_balance = 100
risk_per_trade = 0.2

market_open = '09:30:00'
market_close = '16:00:00'
force_exit_time = '15:45:00'

def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, prepost=False)
    df.columns = df.columns.droplevel(1)
    df.index = df.index.tz_convert('America/New_York')
    df['date'] = df.index.date
    df['time'] = df.index.time
    return df

def get_daily_sessions(df):
    return sorted(df['date'].unique())
   