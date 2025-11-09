# main.py
from pathlib import Path
from config import (BacktestConfig, DataConfig, StrategyConfig, 
                   OrderConfig, PositionConfig, CostConfig, ChartConfig)
from csv_data_loader import CSVDataLoader
from data_aggregator import DataAggregator
from strategy_engine import StrategyEngine
from order_simulator import OrderSimulator
from position_manager import PositionManager
from cost_calculator import CostCalculator
from pnl_tracker import PnLTracker
from performance_analyzer import PerformanceAnalyzer
from report_generator import ReportGenerator

def main():
    # ======================
    # 配置
    # ======================
    csv_file = Path(r"E:\school\4998\crawler\stock\AAPL_1m_20251107.csv")
    output_folder = Path(r"E:\school\4998\backtesting\test")
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 初始化配置
    config = BacktestConfig(
        data=DataConfig(timeframe='15min'),
        strategy=StrategyConfig(buy_threshold=0.95, sell_threshold=1.05),
        order=OrderConfig(slippage_pct=0.001),
        position=PositionConfig(position_type='fixed_capital', capital_pct=0.95, initial_capital=100000),
        cost=CostConfig(commission_type='percentage', commission_pct=0.001),
        chart=ChartConfig()
    )
    
    # ======================
    # 1. 加载1分钟数据
    # ======================
    print("\n=== LOADING 1M DATA ===")
    loader = CSVDataLoader()
    df_1min = loader.load_1m_data(csv_file)
    ticker, _ = loader.extract_metadata(csv_file)
    print(f"Loaded {len(df_1min)} 1m bars for {ticker}")
    
    # ======================
    # 2. 重采样到目标时间框架
    # ======================
    print(f"\n=== RESAMPLING TO {config.data.timeframe} ===")
    aggregator = DataAggregator()
    df_tf = aggregator.resample_to_timeframe(df_1min, config.data.timeframe)
    print(f"Resampled to {len(df_tf)} bars")
    
    # ======================
    # 3. 生成策略信号
    # ======================
    print("\n=== GENERATING SIGNALS ===")
    strategy = StrategyEngine(config.strategy)
    df_tf = strategy.generate_signals(df_tf)
    signal_count = (df_tf['Signal'] != 0).sum()
    print(f"Generated {signal_count} signals")
    
    # ======================
    # 4. 初始化组件
    # ======================
    order_sim = OrderSimulator(df_1min, config.order)
    position_mgr = PositionManager(config.position)
    cost_calc = CostCalculator(config.cost)
    pnl_tracker = PnLTracker()
    perf_analyzer = PerformanceAnalyzer(config.position.initial_capital)
    
    # ======================
    # 5. 回测循环
    # ======================
    print("\n=== RUNNING BACKTEST ===")
    for i, (timestamp, row) in enumerate(df_tf.iterrows()):
        signal = int(row['Signal'])
        
        if signal != 0:
            # 计算仓位大小
            shares = position_mgr.calculate_position_size(row['Close'], signal)
            
            if shares > 0:
                # 模拟订单执行
                order_result = order_sim.simulate_order(timestamp, signal, shares)
                
                if order_result:
                    # 计算成本
                    costs = cost_calc.calculate_total_cost(
                        order_result, row['bid'], row['ask']
                    )
                    
                    # 更新持仓
                    position_mgr.update_position(order_result, costs['commission'])
                    
                    # 记录交易
                    entry_price = position_mgr.avg_cost if signal == -1 else None
                    pnl_tracker.record_trade(order_result, costs, entry_price)
                    
                    print(f"{order_result['signal_type']} executed: "
                          f"{order_result['filled_shares']} shares @ "
                          f"${order_result['execution_price']:.2f} "
                          f"(cost: ${costs['total_cost']:.2f})")
        
        # 更新权益曲线
        current_equity = position_mgr.get_equity(row['Close'])
        perf_analyzer.update_equity(timestamp, current_equity)
    
    # ======================
    # 6. 性能分析
    # ======================
    print("\n=== CALCULATING PERFORMANCE ===")
    trades_df = pnl_tracker.get_trades_df()
    metrics = perf_analyzer.calculate_metrics(trades_df)
    
    print("\n=== PERFORMANCE METRICS ===")
    for key, value in metrics.items():
        if 'pct' in key or 'ratio' in key:
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
    
    # ======================
    # 7. 生成报告
    # ======================
    print("\n=== GENERATING REPORTS ===")
    report_gen = ReportGenerator(config.chart)
    
    # 保存交易明细
    report_gen.save_trades_csv(trades_df, output_folder / f"{ticker}_trades.csv")
    
    # 保存性能报告
    report_gen.generate_html_report(metrics, output_folder / f"{ticker}_performance.html")
    
    # 绘制权益曲线
    equity_df = perf_analyzer.get_equity_df()
    report_gen.plot_equity_curve(equity_df, output_folder / f"{ticker}_equity_curve.png")
    
    # 绘制价格图表
    title = f"{ticker} {config.data.timeframe} Chart with Signals"
    report_gen.plot_price_chart_with_signals(
        df_tf, trades_df, output_folder / f"{ticker}_chart.png", title
    )
    
    print("\n=== BACKTEST COMPLETE ===")

if __name__ == "__main__":
    main()