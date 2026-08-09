import yfinance as yf
import pandas as pd

ticker = 'PLTR'
period = '2y'
interval = '1d'

stop_loss = 0.35
take_profit = 0.7
max_hold = 5
vol_multiplier = 1.2
leverage = 4.0

starting_balance = 50
risk_per_trade = 1

def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
    df['ma9'] = df['Close'].rolling(9).mean()
    df['ma20'] = df['Close'].rolling(20).mean()
    df['vol_avg20'] = df['Volume'].rolling(20).mean()
    df['cross_up'] = (df['ma9'] > df['ma20']) & (df['ma9'].shift(1) <= df['ma20'].shift(1))
    df['cross_down'] = (df['ma9'] < df['ma20']) & (df['ma9'].shift(1) >= df['ma20'].shift(1))
    df['vol_confirm'] = df['Volume'] > vol_multiplier * df['vol_avg20']
    df['buy_call'] = df['cross_up'] & df['vol_confirm']
    df['buy_put'] = df['cross_down'] & df['vol_confirm']
    return df.dropna(subset=['ma9', 'ma20', 'vol_avg20']).reset_index()

