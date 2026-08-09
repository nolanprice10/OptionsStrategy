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
