# order_simulator.py
import pandas as pd
import numpy as np
from typing import Literal
from config import OrderConfig

class OrderSimulator:
    """模拟订单执行"""
    
    def __init__(self, df_1m: pd.DataFrame, config: OrderConfig):
        self.df_1m = df_1m
        self.config = config
    
    def simulate_order(self, 
                      signal_time: pd.Timestamp, 
                      signal_type: Literal[1, -1],
                      shares: int) -> dict:
        """
        模拟订单执行
        
        Args:
            signal_time: 信号时间（高时间框架）
            signal_type: 1=买入, -1=卖出
            shares: 交易股数
            
        Returns:
            订单执行结果字典
        """
        # 找到信号时间后的下一个1分钟数据
        future_data = self.df_1m[self.df_1m.index > signal_time]
        
        if future_data.empty:
            return None
        
        # 取下一个1分钟的价格
        next_bar = future_data.iloc[0]
        
        # 买入：使用ask价格；卖出：使用bid价格
        if signal_type == 1:  # 买入
            base_price = next_bar['ask']
        else:  # 卖出
            base_price = next_bar['bid']
        
        # 添加滑点
        slippage = base_price * self.config.slippage_pct * (1 if signal_type == 1 else -1)
        execution_price = base_price + slippage
        
        # 部分成交模拟
        if np.random.random() < self.config.partial_fill_prob:
            filled_shares = int(shares * np.random.uniform(0.5, 0.9))
        else:
            filled_shares = shares
        
        return {
            'signal_time': signal_time,
            'execution_time': next_bar.name,
            'signal_type': 'BUY' if signal_type == 1 else 'SELL',
            'base_price': base_price,
            'execution_price': execution_price,
            'slippage': slippage,
            'requested_shares': shares,
            'filled_shares': filled_shares,
            'total_value': execution_price * filled_shares
        }