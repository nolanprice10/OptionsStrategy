import yfinance as yf
import numpy as np
import pandas as pd

def backtest(ticker, starting_capital=150000, stop_loss=0.08):
    df = yf.download(ticker, period="3y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close']
    else:
        df = df[['Close']]
    close = df[ticker] if ticker in df.columns else df.iloc[:, 0]
    sma200 = close.rolling(200).mean()
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    cash = starting_capital
    shares = 0
    in_position = False
    peak_price = 0
    trades = []
    equity_curve = []

    for date, price in close.items():
        price = float(price)
        sma_current = 