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

def simulate_trade(df, entry_index, direction):
    entry_price = df.loc[entry_index, 'Close']
    entry_ma9, entry_ma20_direction = df.loc[entry_index, 'ma9'], df.loc[entry_index, 'ma20']

    for offset in range(1, max_hold + 1):
        i = entry_index + offset
        if i >= len(df):
            break

        price_now = df.loc[i, 'Close']
        raw_move = (price_now - entry_price) / entry_price
        option_move = raw_move * leverage if direction == 'call' else -raw_move * leverage

        if option_move <= -stop_loss:
            return i, -stop_loss, 'stop_loss'

        if option_move >= take_profit:
            return i, take_profit, 'take_profit'

        ma9_now, ma20_now = df.loc[i, 'ma9'], df.loc[i, 'ma20']
        if direction == 'call' and ma9_now < ma20_now:
            return i, option_move, 'signal_reversal'
        if direction == 'put' and ma9_now > ma20_now:
            return i, option_move, 'signal_reversal'

    i = min(entry_index + max_hold, len(df) - 1)
    price_now = df.loc[i, 'Close']
    raw_move = (price_now - entry_price) / entry_price
    option_move = raw_move * leverage if direction == 'call' else -raw_move * leverage
    return i, option_move, 'time_exit'

