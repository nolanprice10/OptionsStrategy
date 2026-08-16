import yfinance as yf
import numpy as np
import pandas as pd

def backtest(ticker, starting_capital=150000, stop_loss=0.08):
    df = yf.download(ticker, period="1y", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close']
    else:
        df = df[['Close']]
    close = df[ticker] if ticker in df.columns else df.iloc[:, 0]
    sma50 = close.rolling(50).mean()
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    high_20 = close.rolling(20).max().shift(1)
    low_10 = close.rolling(10).min().shift(1)
    tr = close.diff().abs()
    atr = tr.rolling(14).mean()

    cash = starting_capital
    shares = 0
    in_position = False
    peak_price = 0
    trades = []
    equity_curve = []

    for date, price in close.items():
        price = float(price)
        sma_current = sma50.loc[date]
        rsi_current = rsi.loc[date]
        h20_curr = high_20.loc[date]
        l10_curr = low_10.loc[date]
        atr_curr = atr.loc[date]
        if pd.isna(sma_current) or pd.isna(h20_curr) or pd.isna(l10_curr) or pd.isna(atr_curr):
            continue
        if in_position:
            if price > peak_price:
                peak_price = price
            atr_stop = peak_price - (atr_curr * 2)
            if price <= atr_stop or price < l10_curr:
                reason = "ATR Trailing Stop" if price <= atr_stop else "10-day low break"
                cash = shares * price
                trades.append({'Type': 'Sell', 'Date': date, 'Price': price, 'Reason': reason})
                shares = 0
                in_position = False
                peak_price = 0
        elif not in_position:
            if price >= h20_curr and price > sma_current:
                shares = cash / price
                cash = 0
                in_position = True
                peak_price = price
                trades.append({'Type': 'Buy', 'Date': date, 'Price': price, 'Reason': '20-Day breakout'})
        current_value = cash if not in_position else shares * price
        equity_curve.append(current_value)

    final_value = equity_curve[-1]
    total_return = ((final_value - starting_capital) / starting_capital) * 100
    benchmark_shares = starting_capital / float(close.iloc[49])
    benchmark_final = benchmark_shares * float(close.iloc[-1])
    benchmark_return = ((benchmark_final - starting_capital) / starting_capital) * 100
    eq_series = pd.Series(equity_curve)
    rolling_max = eq_series.cummax()
    drawdowns = (eq_series - rolling_max) / rolling_max
    max_drawdown = drawdowns.min()*100

    print(f"\n" + "="*50)
    print(f"Backtest Summary for {ticker} (1 year):")
    print("="*50)
    print(f"Starting Capital: ${starting_capital:,.2f}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Buy & Hold Value: ${benchmark_final:,.2f} ({benchmark_return:.2f}%)")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Total Trades: {len(trades)}")
    print("="*50)

    return pd.DataFrame(trades)

trade_log = backtest('TQQQ', starting_capital=150000)
if not trade_log.empty:
    print("\nRecent Trades:")
    print(trade_log.tail(6).to_string(index=False))
    