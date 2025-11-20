from futu import *

# Step 1: Initialize the quote context (assumes OpenD is running on localhost:11111)
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

# Step 2: Request historical 1-minute K-line data
# Parameters: code='US.AAPL', start/end in YYYY-MM-DD, kline_type=KLType.K_1M, max_count=None for all data
ret, data, page_req_key = quote_ctx.request_history_kline(
    code='US.AAPL',
    start='2025-10-02',
    end='2025-10-03',
    kline_type=KLType.K_1M,
    max_count=None  # Fetch all available bars in the range
)

# Step 3: Handle the initial response and print data if successful
if ret == RET_OK:
    print("Initial data fetched successfully:")
    print(data)  # Prints the pandas DataFrame with columns: time_key, open, high, low, close, volume, etc.
else:
    print('Error in initial request:', data)

# Step 4: Handle pagination to fetch all pages if more data exists
while page_req_key is not None:
    ret, data, next_page_key = quote_ctx.request_history_kline(page_req_key=page_req_key)
    if ret == RET_OK:
        print("\nAdditional page data:")
        print(data)
    else:
        print('Error in pagination:', data)
    page_req_key = next_page_key  # Update for next iteration

# Step 5: Close the connection
quote_ctx.close()
print("\nConnection closed.")