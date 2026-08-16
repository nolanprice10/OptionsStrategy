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
        sma_current = sma200.loc[date]
        rsi_current = rsi.loc[date]
        if pd.isna(sma_current) or pd.isna(rsi_current):
            equity_curve.append(cash)
            continue
        if in_position:
            if price > peak_price:
                peak_price = price
            stop_price = peak_price * (1 - stop_loss)
            if price <= stop_price or price < sma_current:
                reason = "Trailing Stop" if price <= stop_price else "Trend line break"
                cash = shares * price
                trades.append({'Type': 'Sell', 'Date': date, 'Price': price, 'Reason': reason})
                shares = 0
                in_position = False
                peak_price = 0
        elif not in_position:
            if price > sma_current and rsi_current < 65:
                shares = cash / price
                cash = 0
                in_position = True
                peak_price = price
                trades.append({'Type': 'Buy', 'Date': date, 'Price': price, 'Reason': 'Trend/RSI Buy'})
        current_value = cash if not in_position else shares * price
        equity_curve.append(current_value)

    final_value = equity_curve[-1]
    total_return = ((final_value - starting_capital) / starting_capital) * 100
    benchmark_shares = starting_capital / float(close.iloc[200])
    benchmark_final = benchmark_shares * float(close.iloc[-1])
    benchmark_return = ((benchmark_final - starting_capital) / starting_capital) * 100
    
    