# main.py (just update the strategy selection part)
import pandas as pd
from pathlib import Path
from config import BacktestConfig, DataConfig
from csv_data_loader import CSVDataLoader
from opening_momentum_strategy import OpeningMomentumStrategy
from intraday_mean_reversion_strategy import IntradayMeanReversionStrategy
from momentum_breakout_strategy import MomentumBreakoutStrategy  # Add this import
from order_simulator import OrderSimulator
from position_manager import PositionManager
from cost_calculator import CostCalculator
from pnl_tracker import PnLTracker
from performance_analyzer import PerformanceAnalyzer
from report_generator import ReportGenerator

# ========== STRATEGY SELECTION VARIABLE ==========
# Change this variable to select which strategy to run:
# Options: 'opening_momentum', 'mean_reversion', 'momentum_breakout'
SELECTED_STRATEGY = 'momentum_breakout'  # ← CHANGE THIS LINE TO SWITCH STRATEGIES
# =================================================

def run_backtest(strategy_type: str = SELECTED_STRATEGY, config: BacktestConfig = None):
    """
    Run backtest for specified strategy on 1-minute data
    
    Args:
        strategy_type: 'opening_momentum', 'mean_reversion', or 'momentum_breakout'
        config: BacktestConfig instance. If None, uses default
    """
    if config is None:
        config = BacktestConfig()
        # Override to use 1min timeframe
        config.data.timeframe = '1min'
    
    strategy_names = {
        'opening_momentum': '开盘认知突破策略',
        'mean_reversion': '日内均值回归策略',
        'momentum_breakout': '动量突破策略'
    }
    
    print("=" * 80)
    print(f"{strategy_names[strategy_type]}回测 ({strategy_type.replace('_', ' ').title()} Strategy Backtest)")
    print("=" * 80)
    
    # ========== Step 1: Load Data ==========
    print("\n[1/7] Loading 1-minute data...")
    loader = CSVDataLoader()
    df_1min = loader.load_1m_data(config.path.csv_file)
    ticker, _ = loader.extract_metadata(config.path.csv_file)
    print(f"✓ Loaded {len(df_1min)} bars for {ticker}")
    print(f"  Date range: {df_1min.index[0]} to {df_1min.index[-1]}")
    
    # ========== Step 2: Initialize Strategy ==========
    print("\n[2/7] Initializing strategy...")
    if strategy_type == 'opening_momentum':
        strategy = OpeningMomentumStrategy(
            opening_range_minutes=30,    # First 30 minutes define opening range
            volume_threshold=1.5,         # Volume must be 1.5x average
            breakout_threshold=0.002,     # 0.2% above opening high
            profit_target_pct=0.01,       # 1% profit target
            stop_loss_pct=0.005           # 0.5% stop loss
        )
    elif strategy_type == 'mean_reversion':
        strategy = IntradayMeanReversionStrategy(
            period=20,                    # 20-period moving average
            std_multiplier=2.0,           # 2 standard deviations
            profit_target_pct=0.01,       # 1% profit target
            stop_loss_pct=0.005           # 0.5% stop loss
        )
    else:  # momentum_breakout
        strategy = MomentumBreakoutStrategy(
            lookback_period=10,           # 10-minute momentum lookback
            momentum_threshold=0.003,     # 0.3% momentum threshold
            volume_multiplier=1.5,        # 1.5x volume surge
            profit_target_pct=0.008,      # 0.8% profit target
            stop_loss_pct=0.004           # 0.4% stop loss
        )
    
    print(f"✓ Strategy: {strategy.get_strategy_name()}")
    print(f"  Parameters: {strategy.get_parameters()}")
    
    # ========== Step 3: Generate Signals ==========
    print("\n[3/7] Generating trading signals...")
    df_with_signals = strategy.calculate_signals(df_1min)
    
    buy_signals = (df_with_signals['Signal'] == 1).sum()
    sell_signals = (df_with_signals['Signal'] == -1).sum()
    print(f"✓ Generated signals: {buy_signals} BUY, {sell_signals} SELL")
    
    # ========== Step 4: Initialize Components ==========
    print("\n[4/7] Initializing backtest components...")
    order_sim = OrderSimulator(df_1min, config.order)
    position_mgr = PositionManager(config.position)
    cost_calc = CostCalculator(config.cost)
    pnl_tracker = PnLTracker()
    perf_analyzer = PerformanceAnalyzer(config.position.initial_capital)
    print(f"✓ Initial capital: ${config.position.initial_capital:,.2f}")
    
    # ========== Step 5: Execute Backtest ==========
    print("\n[5/7] Executing backtest...")
    signal_times = df_with_signals[df_with_signals['Signal'] != 0].index
    
    executed_trades = 0
    entry_price = None
    
    for signal_time in signal_times:
        signal_type = df_with_signals.loc[signal_time, 'Signal']
        current_price = df_with_signals.loc[signal_time, 'Close']
        
        # Update equity
        equity = position_mgr.get_equity(current_price)
        perf_analyzer.update_equity(signal_time, equity)
        
        # Calculate position size
        shares = position_mgr.calculate_position_size(current_price, signal_type)
        
        if shares == 0:
            continue
        
        # Simulate order execution
        order_result = order_sim.simulate_order(signal_time, signal_type, shares)
        
        if order_result is None:
            continue
        
        # Calculate costs
        bid = df_1min.loc[order_result['execution_time'], 'bid']
        ask = df_1min.loc[order_result['execution_time'], 'ask']
        costs = cost_calc.calculate_total_cost(order_result, bid, ask)
        
        # Update position
        position_mgr.update_position(order_result, costs['commission'])
        
        # Track P&L
        if signal_type == 1:  # BUY
            entry_price = order_result['execution_price']
            pnl_tracker.record_trade(order_result, costs)
        else:  # SELL
            pnl_tracker.record_trade(order_result, costs, entry_price)
            entry_price = None
        
        executed_trades += 1
    
    print(f"✓ Executed {executed_trades} trades")
    
    # Final equity update
    final_price = df_1min['Close'].iloc[-1]
    final_equity = position_mgr.get_equity(final_price)
    perf_analyzer.update_equity(df_1min.index[-1], final_equity)
    
    # ========== Step 6: Calculate Performance Metrics ==========
    print("\n[6/7] Calculating performance metrics...")
    trades_df = pnl_tracker.get_trades_df()
    metrics = perf_analyzer.calculate_metrics(trades_df)
    
    print(f"\n{'─' * 60}")
    print("Performance Summary:")
    print(f"{'─' * 60}")
    print(f"  Initial Capital:    ${metrics['initial_capital']:>12,.2f}")
    print(f"  Final Equity:       ${metrics['final_equity']:>12,.2f}")
    print(f"  Total Return:       {metrics['total_return_pct']:>12.2f}%")
    print(f"  Annual Return:      {metrics['annual_return_pct']:>12.2f}%")
    print(f"  Max Drawdown:       {metrics['max_drawdown_pct']:>12.2f}%")
    print(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:>12.2f}")
    print(f"  Win Rate:           {metrics['win_rate_pct']:>12.2f}%")
    print(f"  Total Trades:       {metrics['total_trades']:>12}")
    print(f"  Realized P&L:       ${pnl_tracker.get_realized_pnl():>12,.2f}")
    print(f"{'─' * 60}")
    
    # ========== Step 7: Generate Reports ==========
    print("\n[7/7] Generating reports...")
    report_gen = ReportGenerator(config.chart)
    
    # Save trades CSV
    trades_output = config.path.output_folder / f"{ticker}_{strategy.get_strategy_name()}_trades.csv"
    report_gen.save_trades_csv(trades_df, trades_output)
    
    # Save equity curve CSV
    equity_df = perf_analyzer.get_equity_df()
    equity_output = config.path.output_folder / f"{ticker}_{strategy.get_strategy_name()}_equity.csv"
    equity_df.to_csv(equity_output, index=False)
    print(f"Equity curve saved: {equity_output}")
    
    # Generate price chart with signals
    chart_output = config.path.output_folder / f"{ticker}_{strategy.get_strategy_name()}_chart.png"
    try:
        report_gen.plot_price_chart_with_signals(
            df=df_with_signals,
            trades_df=trades_df,
            output_path=chart_output,
            title=f"{ticker} - {strategy.get_strategy_name()} - 1min Chart"
        )
    except Exception as e:
        print(f"Warning: Chart generation failed: {e}")
    
    # Generate HTML performance report
    html_output = config.path.output_folder / f"{ticker}_{strategy.get_strategy_name()}_report.html"
    report_gen.generate_html_report(metrics, html_output, 
                                    title=f"{ticker} - {strategy.get_strategy_name()} Report")
    
    print("\n" + "=" * 80)
    print("✓ Backtest completed successfully!")
    print(f"✓ All reports saved to: {config.path.output_folder}")
    print("=" * 80)
    
    return {
        'metrics': metrics,
        'trades_df': trades_df,
        'equity_df': equity_df,
        'df_with_signals': df_with_signals
    }


if __name__ == "__main__":
    # Create custom config
    config = BacktestConfig()
    config.data.timeframe = '1min'  # Use 1-minute data
    config.position.initial_capital = 100000.0
    config.position.capital_pct = 0.95  # Use 95% of capital per trade
    config.order.slippage_pct = 0.001  # 0.1% slippage
    config.cost.commission_pct = 0.001  # 0.1% commission
    
    # Run only the selected strategy
    print(f"Running {SELECTED_STRATEGY.replace('_', ' ').title()} Strategy...")
    results = run_backtest(SELECTED_STRATEGY, config)
    
    print(f"\n✓ {SELECTED_STRATEGY.replace('_', ' ').title()} backtest finished. Check the output folder for detailed reports.")