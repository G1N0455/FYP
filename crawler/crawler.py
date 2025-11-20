import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# Define the stock symbol and interval
stock_symbol = "TSLA"
interval = "1m"  # Options: '1m', '5m', '10m', '15m', '30m', '60m', '1d'

# Validate interval
valid_intervals = ['1m', '5m', '10m', '15m', '30m', '60m', '1d']
if interval not in valid_intervals:
    raise ValueError(f"Invalid interval '{interval}'. Must be one of: {', '.join(valid_intervals)}")

# Set total date range you want to fetch
end_date = datetime.now().date()
total_days_back = 365  # How many days of 1m data you want (will fetch in chunks)

# Determine chunk size based on interval
if interval == '1m':
    chunk_days = 6  # Fetch 6 days at a time to be safe (Yahoo allows 7-8)
elif interval in ['5m', '10m', '15m', '30m']:
    chunk_days = 59
elif interval == '60m':
    chunk_days = 729
else:  # '1d'
    chunk_days = 365 * 10

# Calculate number of chunks needed
num_chunks = (total_days_back + chunk_days - 1) // chunk_days

# Get current working directory and create stock folder
#current_dir = os.getcwd()
#stock_dir = os.path.join(current_dir, "stock")
stock_dir = r"E:\school\4998\crawler\stock"
os.makedirs(stock_dir, exist_ok=True)

# List to store all data chunks
all_data = []

print(f"Fetching {total_days_back} days of {interval} data in {num_chunks} chunks...")

# Fetch data in chunks
for i in range(num_chunks):
    chunk_end = end_date - timedelta(days=i * chunk_days)
    chunk_start = chunk_end - timedelta(days=chunk_days)
    
    # Don't go beyond total_days_back
    if (end_date - chunk_start).days > total_days_back:
        chunk_start = end_date - timedelta(days=total_days_back)
    
    print(f"Fetching chunk {i+1}/{num_chunks}: {chunk_start} to {chunk_end}")
    
    try:
        chunk_data = yf.download(
            stock_symbol, 
            start=chunk_start, 
            end=chunk_end, 
            interval=interval,
            progress=False
        )
        
        if not chunk_data.empty:
            all_data.append(chunk_data)
            print(f"  Downloaded {len(chunk_data)} rows")
        else:
            print(f"  No data available for this period")
        
        # Add a small delay to avoid rate limiting
        if i < num_chunks - 1:
            time.sleep(1)
            
    except Exception as e:
        print(f"  Error fetching chunk: {str(e)}")
        continue

# Check if we got any data
if not all_data:
    raise ValueError(f"No data found for stock symbol '{stock_symbol}' with interval '{interval}'.")

# Merge all chunks and remove duplicates
merged_data = pd.concat(all_data)
merged_data = merged_data[~merged_data.index.duplicated(keep='first')]
merged_data = merged_data.sort_index()

# Format end date for filename
end_date_str = end_date.strftime("%Y%m%d")

# Define the output CSV file path
csv_filename = os.path.join(stock_dir, f"{stock_symbol}_{interval}_{end_date_str}.csv")

# Save merged data to CSV
merged_data.to_csv(csv_filename)

print(f"\n✓ Stock data for {stock_symbol} with interval {interval} saved to {csv_filename}")
print(f"Data shape: {merged_data.shape}")
print(f"Date range: {merged_data.index.min()} to {merged_data.index.max()}")