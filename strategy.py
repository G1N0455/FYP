# strategy.py
import pandas as pd
import numpy as np
from typing import List, Dict
from config import StrategyConfig

class Strategy:
    def __init__(self, config: StrategyConfig):
        self.config = config
        
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号
        使用双均线交叉策略：
        - 当短期均线上穿长期均线时，产生买入信号
        - 当短期均线下穿长期均线时，产生卖出信号
        """
        signals = df.copy()
        
        # 计算移动平均线
        signals['SMA_short'] = signals['Close'].rolling(window=self.config.sma_short).mean()
        signals['SMA_long'] = signals['Close'].rolling(window=self.config.sma_long).mean()
        
        # 初始化信号列
        signals['signal'] = 0
        signals['position'] = 0
        
        # 生成信号
        # 1 = 买入信号, -1 = 卖出信号
        for i in range(1, len(signals)):
            if pd.notna(signals['SMA_short'].iloc[i]) and pd.notna(signals['SMA_long'].iloc[i]):
                # 金叉：短期均线上穿长期均线 -> 买入
                if (signals['SMA_short'].iloc[i] > signals['SMA_long'].iloc[i] and 
                    signals['SMA_short'].iloc[i-1] <= signals['SMA_long'].iloc[i-1]):
                    signals.loc[signals.index[i], 'signal'] = 1
                    
                # 死叉：短期均线下穿长期均线 -> 卖出
                elif (signals['SMA_short'].iloc[i] < signals['SMA_long'].iloc[i] and 
                      signals['SMA_short'].iloc[i-1] >= signals['SMA_long'].iloc[i-1]):
                    signals.loc[signals.index[i], 'signal'] = -1
        
        # 计算持仓状态
        signals['position'] = signals['signal'].replace(0, np.nan).ffill().fillna(0)
        
        print(f"Generated {(signals['signal'] != 0).sum()} signals")
        return signals


class MomentumStrategy(Strategy):
    """动量策略：基于RSI指标"""
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = df.copy()
        
        # 计算RSI
        delta = signals['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        signals['RSI'] = 100 - (100 / (1 + rs))
        
        # 初始化信号
        signals['signal'] = 0
        signals['position'] = 0
        
        # 生成信号
        # RSI < 30: 超卖 -> 买入
        # RSI > 70: 超买 -> 卖出
        for i in range(1, len(signals)):
            if pd.notna(signals['RSI'].iloc[i]):
                if signals['RSI'].iloc[i] < 30 and signals['RSI'].iloc[i-1] >= 30:
                    signals.loc[signals.index[i], 'signal'] = 1
                elif signals['RSI'].iloc[i] > 70 and signals['RSI'].iloc[i-1] <= 70:
                    signals.loc[signals.index[i], 'signal'] = -1
        
        signals['position'] = signals['signal'].replace(0, np.nan).ffill().fillna(0)
        
        print(f"Generated {(signals['signal'] != 0).sum()} signals (Momentum/RSI)")
        return signals


class MeanReversionStrategy(Strategy):
    """均值回归策略：基于布林带"""
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = df.copy()
        
        # 计算布林带
        window = 20
        signals['SMA'] = signals['Close'].rolling(window=window).mean()
        signals['STD'] = signals['Close'].rolling(window=window).std()
        signals['Upper_Band'] = signals['SMA'] + (2 * signals['STD'])
        signals['Lower_Band'] = signals['SMA'] - (2 * signals['STD'])
        
        # 初始化信号
        signals['signal'] = 0
        signals['position'] = 0
        
        # 生成信号
        # 价格触及下轨 -> 买入
        # 价格触及上轨 -> 卖出
        for i in range(1, len(signals)):
            if pd.notna(signals['Lower_Band'].iloc[i]):
                if signals['Close'].iloc[i] <= signals['Lower_Band'].iloc[i]:
                    signals.loc[signals.index[i], 'signal'] = 1
                elif signals['Close'].iloc[i] >= signals['Upper_Band'].iloc[i]:
                    signals.loc[signals.index[i], 'signal'] = -1
        
        signals['position'] = signals['signal'].replace(0, np.nan).ffill().fillna(0)
        
        print(f"Generated {(signals['signal'] != 0).sum()} signals (Mean Reversion)")
        return signals