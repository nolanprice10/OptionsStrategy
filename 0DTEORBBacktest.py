import yfinance as yf
import pandas as pd

ticker = 'QQQ'
interval = '5m'
period = '60d'

or_minutes = 15
or_bars = or_minutes // 5

stop_loss = 0.2
take_profit = 0.45
leverage = 12.0

starting_balance = 50
risk_per_trade = 1

market_open = '09:30:00'
market_close = '16:00:00'
force_exit_time = '15:45:00'

def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, prepost=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    df.index = df.index.tz_convert('America/New_York')
    df['date'] = df.index.date
    df['time'] = df.index.time
    df['Vol_SMA10'] = df['Volume'].rolling(10).mean()
    return df

def get_daily_sessions(df):
    return sorted(df['date'].unique())

def simulate_day(day_df, day):
    day_df = day_df.between_time(market_open, market_close)
    if len(day_df) < or_bars + 1:
        return None

    opening_range = day_df.iloc[:or_bars]
    or_high = opening_range['High'].max()
    or_low = opening_range['Low'].min()

    post_or = day_df.iloc[or_bars:]
    force_exit = pd.Timestamp.combine(day, pd.Timestamp(force_exit_time).time()).tz_localize('America/New_York')

    direction = None
    entry_price = None
    entry_time = None

    for ts, row in post_or.iterrows():
        vol_avg = row['Vol_SMA10'] if not pd.isna(row['Vol_SMA10']) else row['Volume']
        volume_confirmed = row['Volume'] >= (2.0 * vol_avg)
        if row['Close'] > or_high:
            direction = 'call'
            entry_price = row['Close']
            entry_time = ts
            break
        if row['Close'] < or_low:
            direction = 'put'
            entry_price = row['Close']
            entry_time = ts
            break

    if direction is None:
        return None

    remaining = day_df[day_df.index > entry_time]

    for ts, row in remaining.iterrows():
        high_move = (row['High'] - entry_price) / entry_price
        low_move = (row['Low'] - entry_price) / entry_price
        
        if direction == 'call':
            max_option_pnl = high_move * leverage
            min_option_pnl = low_move * leverage
        else:
            max_option_pnl = -low_move * leverage
            min_option_pnl = -high_move * leverage

        if min_option_pnl <= -stop_loss:
            return {'entry_time': entry_time, 'exit_time': ts, 'direction': direction,
                    'pnl': -stop_loss, 'exit_reason': 'stop_loss'}

        if max_option_pnl >= take_profit:
            return {'entry_time': entry_time, 'exit_time': ts, 'direction': direction,
                    'pnl': take_profit, 'exit_reason': 'take_profit'}

        if ts >= force_exit:
            close_move = (row['Close'] - entry_price) / entry_price
            close_pnl = close_move * leverage if direction == 'call' else -close_move * leverage
            return {'entry_time': entry_time, 'exit_time': ts, 'direction': direction,
                    'pnl': close_pnl, 'exit_reason': 'eod_exit'}

    last_row = day_df.iloc[-1]
    raw_move = (last_row['Close'] - entry_price) / entry_price
    option_move = raw_move * leverage if direction == 'call' else -raw_move * leverage
    return {'entry_time': entry_time, 'exit_time': last_row.name, 'direction': direction,
            'pnl': option_move, 'exit_reason': 'eod_exit'}

def run_backtest():
    df = load_data(ticker, period, interval)
    sessions = get_daily_sessions(df)

    trades = []
    balance = starting_balance

    for day in sessions:
        day_df = df[df['date'] == day]
        result = simulate_day(day_df, day)
        if result is None:
            continue

        risk_amount = balance * risk_per_trade
        pnl_dollars = result['pnl'] * risk_amount
        balance += pnl_dollars

        trades.append({
            'date': day,
            'entry_time': result['entry_time'],
            'exit_time': result['exit_time'],
            'direction': result['direction'],
            'pnl': round(result['pnl'] * 100, 2),
            'pnl_dollars': round(pnl_dollars, 2),
            'balance_after_trade': round(balance, 2),
            'exit_reason': result['exit_reason'],
        })

        if balance <= 0:
            break

    return pd.DataFrame(trades), balance

def print_summary(trades_df, final_balance):
    if trades_df.empty:
        print("No trades were made.")
        return

    wins = trades_df[trades_df['pnl_dollars'] > 0]
    losses = trades_df[trades_df['pnl_dollars'] <= 0]

    print(f"\n{'='*50}")
    print(f"0DTE ORB Scalp Backtest: {ticker}")
    print(f"{'='*50}")
    print(f"Total Trades: {len(trades_df)}")
    print(f"Win rate: {len(wins) / len(trades_df) * 100:.2f}%")
    if len(wins):
        print(f"Avg win: {wins['pnl'].mean():.2f}%")
    if len(losses):
        print(f"Avg loss: {losses['pnl'].mean():.2f}%")
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