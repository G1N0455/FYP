# opening_momentum_strategy.py
import pandas as pd
import numpy as np
from typing import Literal

class OpeningMomentumStrategy:
    """
    開盤動能突破策略 (Opening Momentum Breakout Strategy)
    
    High-frequency strategy that trades momentum breakouts in the first hour of trading.
    
    Logic:
    1. Calculate opening range (first N minutes high/low)
    2. Monitor volume surge (volume > avg_volume * threshold)
    3. BUY when price breaks above opening range high with strong volume
    4. SELL when price breaks below opening range low OR hits profit target/stop loss
    
    Parameters:
    - opening_range_minutes: Minutes to define opening range (default: 30)
    - volume_threshold: Volume multiplier for surge detection (default: 1.5)
    - breakout_threshold: Price % above opening high to trigger buy (default: 0.2%)
    - profit_target_pct: Take profit % (default: 1.0%)
    - stop_loss_pct: Stop loss % (default: 0.5%)
    """
    
    def __init__(self,
                 opening_range_minutes: int = 30,
                 volume_threshold: float = 1.5,
                 breakout_threshold: float = 0.002,  # 0.2%
                 profit_target_pct: float = 0.01,    # 1.0%
                 stop_loss_pct: float = 0.005):       # 0.5%
        
        self.opening_range_minutes = opening_range_minutes
        self.volume_threshold = volume_threshold
        self.breakout_threshold = breakout_threshold
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        
        # State variables
        self.in_position = False
        self.entry_price = 0.0
        self.opening_high = 0.0
        self.opening_low = 0.0
        self.opening_range_set = False
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals for 1-minute data
        
        Args:
            df: 1-minute OHLCV DataFrame with DatetimeIndex
            
        Returns:
            DataFrame with 'Signal' column (1=BUY, -1=SELL, 0=HOLD)
        """
        df = df.copy()
        df['Signal'] = 0
        
        # Calculate rolling average volume (20-period)
        df['AvgVolume'] = df['Volume'].rolling(window=20, min_periods=1).mean()
        
        # Identify market open for each trading day
        df['Date'] = df.index.date
        df['Time'] = df.index.time
        df['MinuteOfDay'] = (df.index.hour * 60 + df.index.minute)
        
        # Group by date and process each day
        for date, day_data in df.groupby('Date'):
            # Get indices for this day
            day_indices = day_data.index
            
            if len(day_indices) < self.opening_range_minutes:
                continue  # Skip if not enough data
            
            # Calculate opening range (first N minutes)
            opening_indices = day_indices[:self.opening_range_minutes]
            opening_data = df.loc[opening_indices]
            
            opening_high = opening_data['High'].max()
            opening_low = opening_data['Low'].min()
            
            # Process rest of the day
            for i, idx in enumerate(day_indices[self.opening_range_minutes:]):
                current_bar = df.loc[idx]
                
                # Skip if already in position (will be handled by exit logic)
                if self.in_position:
                    # Check exit conditions
                    if current_bar['Low'] <= self.entry_price * (1 - self.stop_loss_pct):
                        # Stop loss hit
                        df.loc[idx, 'Signal'] = -1
                        self.in_position = False
                        self.entry_price = 0.0
                    elif current_bar['High'] >= self.entry_price * (1 + self.profit_target_pct):
                        # Profit target hit
                        df.loc[idx, 'Signal'] = -1
                        self.in_position = False
                        self.entry_price = 0.0
                    elif current_bar['Low'] < opening_low:
                        # Price breaks below opening range
                        df.loc[idx, 'Signal'] = -1
                        self.in_position = False
                        self.entry_price = 0.0
                else:
                    # Check entry conditions
                    volume_surge = current_bar['Volume'] > current_bar['AvgVolume'] * self.volume_threshold
                    price_breakout = current_bar['Close'] > opening_high * (1 + self.breakout_threshold)
                    
                    if volume_surge and price_breakout:
                        df.loc[idx, 'Signal'] = 1
                        self.in_position = True
                        self.entry_price = current_bar['Close']
            
            # Close any open positions at end of day
            if self.in_position and len(day_indices) > 0:
                last_idx = day_indices[-1]
                if df.loc[last_idx, 'Signal'] == 0:  # Only if not already closed
                    df.loc[last_idx, 'Signal'] = -1
                self.in_position = False
                self.entry_price = 0.0
        
        # Clean up temporary columns
        df.drop(['Date', 'Time', 'MinuteOfDay', 'AvgVolume'], axis=1, inplace=True)
        
        return df
    
    def get_strategy_name(self) -> str:
        """Return strategy name"""
        return f"OpeningMomentum_{self.opening_range_minutes}min"
    
    def get_parameters(self) -> dict:
        """Return strategy parameters"""
        return {
            'opening_range_minutes': self.opening_range_minutes,
            'volume_threshold': self.volume_threshold,
            'breakout_threshold': self.breakout_threshold,
            'profit_target_pct': self.profit_target_pct,
            'stop_loss_pct': self.stop_loss_pct
        }