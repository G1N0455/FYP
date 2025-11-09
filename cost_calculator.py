# cost_calculator.py
from config import CostConfig

class CostCalculator:
    """计算交易成本"""
    
    def __init__(self, config: CostConfig):
        self.config = config
    
    def calculate_commission(self, order_value: float) -> float:
        """计算手续费"""
        if self.config.commission_type == 'fixed':
            return self.config.commission_fixed
        else:
            return order_value * self.config.commission_pct
    
    def calculate_spread_cost(self, bid: float, ask: float, shares: int) -> float:
        """计算买卖价差成本"""
        return (ask - bid) * shares
    
    def calculate_total_cost(self, order_result: dict, bid: float, ask: float) -> dict:
        """计算总成本"""
        order_value = order_result['total_value']
        commission = self.calculate_commission(order_value)
        slippage_cost = abs(order_result['slippage']) * order_result['filled_shares']
        spread_cost = self.calculate_spread_cost(bid, ask, order_result['filled_shares'])
        
        return {
            'commission': commission,
            'slippage_cost': slippage_cost,
            'spread_cost': spread_cost,
            'total_cost': commission + slippage_cost
        }