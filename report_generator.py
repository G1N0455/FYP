# report_generator.py
import pandas as pd
import numpy as np
import mplfinance as mpf
from pathlib import Path
from typing import Dict, Union
from config import ChartConfig, BacktestConfig
from data_aggregator import DataAggregator
from csv_data_loader import CSVDataLoader

class ReportGenerator:
    def __init__(self, config: ChartConfig):
        self.config = config
    
    def save_trades_csv(self, trades_df: pd.DataFrame, output_path: Path):
        """保存交易记录到CSV"""
        if trades_df.empty:
            empty_df = pd.DataFrame(columns=[
                'timestamp', 'signal_type', 'price', 'shares', 
                'commission', 'slippage', 'total_cost'
            ])
            empty_df.to_csv(output_path, index=False)
        else:
            trades_df.to_csv(output_path, index=True)
        print(f"Trades saved: {output_path}")
    
    def save_performance_html(self, metrics: Dict, output_path: Path):
        """保存性能报告（别名方法）"""
        self.generate_html_report(metrics, output_path)
    
    def _make_signal_markers(self, df: pd.DataFrame) -> list:
        """
        Create mplfinance addplot objects for buy/sell signals.
        Adapted from plotkline.py make_signal_markers function.
        """
        add_plots = []

        # BUY signals
        buy_mask = df['Signal'] == 1
        if buy_mask.any():
            buy_prices = df.loc[buy_mask, 'Low'] * self.config.buy_marker_offset
            buy_series = pd.Series(index=df.index, dtype='float64')
            buy_series.loc[buy_mask] = buy_prices

            add_plots.append(mpf.make_addplot(
                buy_series,
                type='scatter',
                marker='^',
                markersize=120,
                color='lime',
                label='BUY'
            ))

        # SELL signals
        sell_mask = df['Signal'] == -1
        if sell_mask.any():
            sell_prices = df.loc[sell_mask, 'High'] * self.config.sell_marker_offset
            sell_series = pd.Series(index=df.index, dtype='float64')
            sell_series.loc[sell_mask] = sell_prices

            add_plots.append(mpf.make_addplot(
                sell_series,
                type='scatter',
                marker='v',
                markersize=120,
                color='red',
                label='SELL'
            ))

        return add_plots
    
    def plot_price_chart_with_signals(
        self, df: pd.DataFrame, trades_df: pd.DataFrame,
        output_path: Path, title: str = "Price Chart with Signals"
    ):
        """绘制价格图表和交易信号 - 使用mplfinance"""
        
        # 确保df有必要的列
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        # 添加Signal列（如果不存在）
        if 'Signal' not in df.columns:
            df['Signal'] = 0
            
            # 从trades_df映射信号
            if not trades_df.empty and 'signal_type' in trades_df.columns:
                for idx, row in trades_df.iterrows():
                    if idx in df.index:
                        if row['signal_type'] == 'BUY':
                            df.loc[idx, 'Signal'] = 1
                        elif row['signal_type'] == 'SELL':
                            df.loc[idx, 'Signal'] = -1
        
        # 确定图表类型（基于数据点数量）
        num_candles = len(df)
        if num_candles > 100:
            chart_type = 'line'
            print(f"Using line chart (data points: {num_candles} > 100)")
        else:
            chart_type = 'candle'
            print(f"Using candlestick chart (data points: {num_candles} <= 100)")
        
        # 创建mplfinance样式
        style = mpf.make_mpf_style(
            marketcolors=mpf.make_marketcolors(
                up=self.config.style_up_color,
                down=self.config.style_down_color,
                wick='inherit'
            ),
            gridstyle='-',
            gridcolor='lightgray'
        )
        
        # 生成信号标记
        signal_plots = self._make_signal_markers(df)
        
        # 绘制图表
        plot_kwargs = dict(
            type=chart_type,  # Use dynamic chart type
            style=style,
            title=title,
            volume=self.config.volume,
            ylabel='Price (USD)',
            ylabel_lower='Volume',
            savefig=dict(fname=str(output_path), dpi=self.config.dpi, bbox_inches='tight'),
            tight_layout=True
        )
        
        # Only add addplot parameter if there are signals to plot
        if signal_plots:
            plot_kwargs['addplot'] = signal_plots
        
        # Pass df as first positional argument
        mpf.plot(df, **plot_kwargs)
        
        print(f"Price chart saved: {output_path}")
    
    def generate_html_report(
        self, metrics: Dict, output_path: Path,
        title: str = "Backtest Performance Report"
    ):
        """生成HTML性能报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 10px;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-top: 20px;
                }}
                .metric-box {{
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #4CAF50;
                }}
                .metric-label {{
                    font-size: 14px;
                    color: #666;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                }}
                .positive {{ color: #4CAF50; }}
                .negative {{ color: #f44336; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <div class="metric-grid">
                    <div class="metric-box">
                        <div class="metric-label">Initial Capital</div>
                        <div class="metric-value">${metrics['initial_capital']:,.2f}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Final Equity</div>
                        <div class="metric-value">${metrics['final_equity']:,.2f}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Return</div>
                        <div class="metric-value {'positive' if metrics['total_return_pct'] >= 0 else 'negative'}">
                            {metrics['total_return_pct']:.2f}%
                        </div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Annual Return</div>
                        <div class="metric-value {'positive' if metrics['annual_return_pct'] >= 0 else 'negative'}">
                            {metrics['annual_return_pct']:.2f}%
                        </div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Max Drawdown</div>
                        <div class="metric-value negative">{metrics['max_drawdown_pct']:.2f}%</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Sharpe Ratio</div>
                        <div class="metric-value">{metrics['sharpe_ratio']:.2f}</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Win Rate</div>
                        <div class="metric-value">{metrics['win_rate_pct']:.2f}%</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-label">Total Trades</div>
                        <div class="metric-value">{metrics['total_trades']}</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        output_path.write_text(html, encoding='utf-8')
        print(f"Performance report saved: {output_path}")


def gen_kline(config: BacktestConfig = None):
    """
    Generate K-line chart based on config.data.timeframe
    
    Args:
        config: BacktestConfig instance. If None, uses default (15min)
    """
    if config is None:
        config = BacktestConfig()
    
    # Load 1-minute data
    loader = CSVDataLoader()
    df_1min = loader.load_1m_data(config.path.csv_file)
    
    # Extract ticker name from file
    ticker, _ = loader.extract_metadata(config.path.csv_file)
    
    # Get timeframe from config
    timeframe = config.data.timeframe
    
    print(f"\n=== Generating {timeframe} K-line ===")
    
    # Resample data
    aggregator = DataAggregator()
    df_resampled = aggregator.resample_to_timeframe(df_1min, timeframe)
    
    # Save CSV
    csv_output = config.path.output_folder / f"{ticker}_{timeframe}_resampled.csv"
    df_resampled.to_csv(csv_output)
    print(f"CSV saved: {csv_output}")
    
    # Generate chart
    report_gen = ReportGenerator(config.chart)
    empty_trades = pd.DataFrame(columns=['signal_type', 'price', 'shares'])
    chart_output = config.path.output_folder / f"{ticker}_{timeframe}_chart.png"
    
    try:
        report_gen.plot_price_chart_with_signals(
            df=df_resampled,
            trades_df=empty_trades,
            output_path=chart_output,
            title=f"{ticker} {timeframe} K-Line Chart"
        )
        print(f"Chart saved: {chart_output}")
    except Exception as e:
        print(f"Chart generation failed: {e}")