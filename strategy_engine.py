# strategy_engine.py
import pandas as pd
from config import StrategyConfig

class StrategyEngine:
    """策略引擎：在高时间框架生成买卖信号"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        
        Signal: 1=买入, -1=卖出, 0=无信号
        """
        df = df.copy()
        df['prev_close'] = df['Close'].shift(1)
        df['Signal'] = 0
        
        for i in range(1, len(df)):
            close = df['Close'].iloc[i]
            prev = df['prev_close'].iloc[i]
            date = df.index[i]
            
            if pd.notna(prev):
                # 买入信号：价格下跌超过阈值
                if close < prev * self.config.buy_threshold:
                    df.loc[date, 'Signal'] = 1
                    self._log_signal("BUY", date, close, prev)
                # 卖出信号：价格上涨超过阈值
                elif close > prev * self.config.sell_threshold:
                    df.loc[date, 'Signal'] = -1
                    self._log_signal("SELL", date, close, prev)
        
        return df
    
    @staticmethod
    def _log_signal(signal_type: str, date, close: float, prev: float):
        """记录信号生成"""
        pct_change = (close / prev - 1) * 100
        print(f"{signal_type:4s} signal on {date} | "
              f"Close: {close:,.2f} | Prev: {prev:,.2f} ({pct_change:+.2f}%)")