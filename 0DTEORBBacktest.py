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
        price_now = row['Close']
        raw_move = (price_now - entry_price) / entry_price
        option_move = raw_move * leverage if direction == 'call' else -raw_move * leverage

        if option_move <= -stop_loss:
            return {'entry_time': entry_time, 'exit_time': ts, 'direction': direction,
                    'pnl': -stop_loss, 'exit_reason': 'stop_loss'}
        if option_move >= take_profit:
            return {'entry_time': entry_time, 'exit_time': ts, 'direction': direction,
                    'pnl': take_profit, 'exit_reason': 'take_profit'}
        if ts >= force_exit:
            return {'entry_time': entry_time, 'exit_time': ts, 'direction': direction,
                    'pnl': option_move, 'exit_reason': 'eod_exit'}

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
