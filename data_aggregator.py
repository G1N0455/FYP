# data_aggregator.py
import pandas as pd
import numpy as np

class DataAggregator:
    """将1分钟数据重采样为更高时间框架"""
    
    @staticmethod
    def resample_to_timeframe(df_1min: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        重采样1分钟数据到指定时间框架
        
        Args:
            df_1min: 1分钟数据
            timeframe: '15m', '30m', '1h', etc.
        
        Returns:
            重采样后的OHLCV数据 + 平均bid/ask spread
        """
        # OHLCV重采样
        if 'Open' in df_1min.columns:
            ohlc = df_1min['Close'].resample(timeframe).ohlc()
            ohlc.columns = ['Open', 'High', 'Low', 'Close']
            volume = df_1min['Volume'].resample(timeframe).sum()
        else:
            # 如果只有bid/ask，用mid price
            df_1min['mid'] = (df_1min['bid'] + df_1min['ask']) / 2
            ohlc = df_1min['mid'].resample(timeframe).ohlc()
            ohlc.columns = ['Open', 'High', 'Low', 'Close']
            volume = df_1min['volume'].resample(timeframe).sum()
        
        # Bid/Ask重采样（取平均）
        bid_avg = df_1min['bid'].resample(timeframe).mean()
        ask_avg = df_1min['ask'].resample(timeframe).mean()
        
        # 合并
        df_resampled = pd.concat([ohlc, volume, bid_avg, ask_avg], axis=1)
        df_resampled.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'bid', 'ask']
        
        # 计算平均spread
        df_resampled['spread'] = df_resampled['ask'] - df_resampled['bid']
        df_resampled['spread_pct'] = df_resampled['spread'] / df_resampled['Close']
        
        # 移除缺失值
        df_resampled.dropna(inplace=True)
        
        return df_resampled