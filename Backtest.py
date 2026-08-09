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