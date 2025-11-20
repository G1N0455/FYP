# Intraday Trading Strategy Backtesting System (Academic Use)

A lightweight, modular Python backtesting framework designed for **academic research and strategy prototyping** on 1-minute US stock data.

This project implements and compares three classic intraday strategies:
- **Opening Momentum** (Opening Range Breakout + Volume confirmation)
- **Intraday Mean Reversion** (Bollinger Bands style)
- **Momentum Breakout** (Short-term price + volume surge)

All strategies are backtested with realistic execution simulation including:
- Bid/Ask spread
- Slippage & partial fills
- Commission costs
- Position sizing (fixed capital allocation)
- Detailed performance metrics (Sharpe, Sortino, Max DD, Win Rate, etc.)
- Equity curve, trade log, and visualized charts

Perfect for students, researchers, or anyone learning quantitative trading.

## Features

- Clean modular design (data → strategy → execution → reporting)
- 1-minute CSV data loader with synthetic bid/ask
- Resampling to higher timeframes (15min, 30min, 1h, etc.)
- mplfinance charts with buy/sell markers
- HTML performance report + CSV trade logs
- Easy strategy switching via one variable

## Important Notes

**This project is for educational and academic purposes only**.  
It is **not** financial advice and has not been tested in live trading.

### You MUST modify paths before running!

Edit `config.py` and update these lines with your own paths:

```python
csv_file: Path = Path(r"E:\school\4998\backtesting\v2\crawler\stock\AAPL_1m_20251107.csv")
output_folder: Path = Path(r"E:\school\4998\backtesting\v2\test_output")