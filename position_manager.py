# position_manager.py
import pandas as pd
from config import PositionConfig

class PositionManager:
    """管理单一股票持仓"""
    
    def __init__(self, config: PositionConfig):
        self.config = config
        self.cash = config.initial_capital
        self.shares = 0
        self.avg_cost = 0.0
        self.positions_history = []
    
    def calculate_position_size(self, price: float, signal_type: int) -> int:
        """
        计算仓位大小
        
        Args:
            price: 当前价格
            signal_type: 1=买入, -1=卖出
            
        Returns:
            股数
        """
        if signal_type == 1:  # 买入
            if self.config.position_type == 'fixed_shares':
                return self.config.fixed_shares
            else:  # fixed_capital
                available_capital = self.cash * self.config.capital_pct
                return int(available_capital / price)
        else:  # 卖出
            return self.shares  # 全部卖出
    
    def update_position(self, order_result: dict, commission: float):
        """更新持仓状态"""
        signal_type = 1 if order_result['signal_type'] == 'BUY' else -1
        filled_shares = order_result['filled_shares']
        execution_price = order_result['execution_price']
        
        if signal_type == 1:  # 买入
            cost = execution_price * filled_shares + commission
            self.cash -= cost
            
            # 更新平均成本
            total_cost = self.avg_cost * self.shares + execution_price * filled_shares
            self.shares += filled_shares
            self.avg_cost = total_cost / self.shares if self.shares > 0 else 0
            
        else:  # 卖出
            proceeds = execution_price * filled_shares - commission
            self.cash += proceeds
            self.shares -= filled_shares
            
            if self.shares == 0:
                self.avg_cost = 0.0
        
        # 记录持仓变化
        self.positions_history.append({
            'time': order_result['execution_time'],
            'action': order_result['signal_type'],
            'shares': self.shares,
            'cash': self.cash,
            'avg_cost': self.avg_cost
        })
    
    def get_equity(self, current_price: float) -> float:
        """计算当前权益"""
        return self.cash + self.shares * current_price
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """计算未实现盈亏"""
        if self.shares == 0:
            return 0.0
        return (current_price - self.avg_cost) * self.shares