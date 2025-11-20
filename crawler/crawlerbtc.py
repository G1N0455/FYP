import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

# Define the cryptocurrency symbol and interval
crypto_symbol = "BTC-USD"  # Bitcoin symbol on Yahoo Finance
interval = "1d"  # Daily interval

# Validate interval
valid_intervals = ['1m', '5m', '10m', '15m', '30m', '60m', '1d']
if interval not in valid_intervals:
    raise ValueError(f"Invalid interval '{interval}'. Must be one of: {', '.join(valid_intervals)}")

# Set date range for the past 30 days
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)  # Past 30 days

# Format end date for filename
end_date_str = end_date.strftime("%Y%m%d")

# Define the output directory and create it if it doesn't exist
output_dir = r"E:\school\4998\crawler\stock"
os.makedirs(output_dir, exist_ok=True)

# Define the output CSV file path (cryptosymbol_interval_date)
csv_filename = os.path.join(output_dir, f"{crypto_symbol}_{interval}_{end_date_str}.csv")

# Download cryptocurrency data using yfinance
try:
    crypto_data = yf.download(crypto_symbol, start=start_date, end=end_date, interval=interval)
except Exception as e:
    raise ValueError(f"Failed to fetch data for cryptocurrency symbol '{crypto_symbol}'. Ensure the symbol is valid and try again. Error: {str(e)}")

# Check if data is empty (indicating invalid symbol or no data)
if crypto_data.empty:
    raise ValueError(f"No data found for cryptocurrency symbol '{crypto_symbol}' with interval '{interval}'. Please check the symbol or date range (must include trading days).")

# Save raw data to CSV without reindexing (skips missing periods)
crypto_data.to_csv(csv_filename)

print(f"Cryptocurrency data for {crypto_symbol} with interval {interval} saved to {csv_filename}")
print(f"Data shape: {crypto_data.shape}")