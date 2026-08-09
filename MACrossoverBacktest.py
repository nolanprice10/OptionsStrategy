import yfinance as yf
import pandas as pd

ticker = 'SPY'
period = 'max'
interval = '1d'

stop_loss = 0.3
take_profit = 0.7
max_hold = 14
leverage = 4.0

starting_balance = 100
risk_per_trade = 0.3

def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
    df.columns = df.columns.droplevel(1)
    df['ma10'] = df['Close'].rolling(10).mean()
    df['ma30'] = df['Close'].rolling(30).mean()
    df['cross_up'] = (df['ma10'] > df['ma30']) & (df['ma10'].shift(1) <= df['ma30'].shift(1))
    df['cross_down'] = (df['ma10'] < df['ma30']) & (df['ma10'].shift(1) >= df['ma30'].shift(1))
    df['buy_call'] = df['cross_up']
    df['buy_put'] = df['cross_down']
    return df.dropna(subset=['ma10', 'ma30']).reset_index()

def simulate_trade(df, entry_index, direction):
    entry_price = df.loc[entry_index, 'Close']
    entry_ma10, entry_ma30_direction = df.loc[entry_index, 'ma10'], df.loc[entry_index, 'ma30']

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

        ma10_now, ma30_now = df.loc[i, 'ma10'], df.loc[i, 'ma30']
        if direction == 'call' and ma10_now < ma30_now:
            return i, option_move, 'signal_reversal'
        if direction == 'put' and ma10_now > ma30_now:
            return i, option_move, 'signal_reversal'

    i = min(entry_index + max_hold, len(df) - 1)
    price_now = df.loc[i, 'Close']
    raw_move = (price_now - entry_price) / entry_price
    option_move = raw_move * leverage if direction == 'call' else -raw_move * leverage
    return i, option_move, 'time_exit'

def run_backtest(ticker=ticker, period=period, interval=interval):
    df = load_data(ticker, period, interval)

    trades = []
    balance = starting_balance
    i = 0
    while i < len(df) - 1:
        row = df.loc[i]
        if row['buy_call'] or row['buy_put']:
            direction = 'call' if row['buy_call'] else 'put'
            exit_index, pnl, reason = simulate_trade(df, i, direction)

            risk_amount = balance * risk_per_trade
            pnl_dollars = pnl * risk_amount
            balance += pnl_dollars

            trades.append({
                'entry_date': df.loc[i, 'Date'],
                'exit_date': df.loc[exit_index, 'Date'],
                'direction': direction,
                'pnl': round(pnl * 100, 2),
                'pnl_dollars': round(pnl_dollars, 2),
                'balance_after_trade': round(balance, 2),
                'exit_reason': reason,
            })

            i = exit_index + 1
            if balance <= 0:
                break
        else:
            i += 1

    return pd.DataFrame(trades), balance

def print_summary(trades_df, final_balance):
    if trades_df.empty:
        print("No trades were executed.")
        return

    wins = trades_df[trades_df['pnl_dollars'] > 0]
    losses = trades_df[trades_df['pnl_dollars'] <= 0]

    print(f"\n{'='*50}")
    print(f"Backtest Results: {ticker}")
    print(f"{'='*50}")
    print(f"Total Trades: {len(trades_df)}")
    print(f"Win rate: {len(wins) / len(trades_df) * 100:.2f}%")
    print(f"Avg win: {wins['pnl'].mean():.2f}%") if len(wins) else 'Avg win: N/A'
    print(f"Avg loss: {losses['pnl'].mean():.2f}%") if len(losses) else 'Avg loss: N/A'
    print(f"Starting balance: ${starting_balance:.2f}")
    print(f"Final balance: ${final_balance:.2f}")
    print(f"Total return: {(final_balance/starting_balance - 1) * 100:.2f}%")
    print(f"Max single win: {trades_df['pnl_dollars'].max():.2f}")
    print(f"Max single loss: {trades_df['pnl_dollars'].min():.2f}")
    print(f"{'='*50}\n")
    print(trades_df.to_string(index=False))

if __name__ == '__main__':
    trades_df, final_balance = run_backtest()
    print_summary(trades_df, final_balance)