# pnl_tracker.py
import pandas as pd

class PnLTracker:
    """跟踪盈亏"""
    
    def __init__(self):
        self.trades = []
        self.realized_pnl = 0.0
        self.trade_count = 0
    
    def record_trade(self, order_result: dict, costs: dict, entry_price: float = None):
        """记录交易"""
        trade = {
            'trade_id': self.trade_count,
            'execution_time': order_result['execution_time'],
            'signal_type': order_result['signal_type'],
            'execution_price': order_result['execution_price'],
            'filled_shares': order_result['filled_shares'],
            'total_value': order_result['total_value'],
            'commission': costs['commission'],
            'slippage_cost': costs['slippage_cost'],
            'total_cost': costs['total_cost']
        }
        
        # 如果是卖出，计算已实现盈亏
        if order_result['signal_type'] == 'SELL' and entry_price:
            gross_pnl = (order_result['execution_price'] - entry_price) * order_result['filled_shares']
            net_pnl = gross_pnl - costs['total_cost']
            trade['entry_price'] = entry_price
            trade['gross_pnl'] = gross_pnl
            trade['net_pnl'] = net_pnl
            self.realized_pnl += net_pnl
        
        self.trades.append(trade)
        self.trade_count += 1
    
    def get_trades_df(self) -> pd.DataFrame:
        """获取交易明细DataFrame"""
        return pd.DataFrame(self.trades)
    
    def get_realized_pnl(self) -> float:
        """获取已实现盈亏"""
        return self.realized_pnl