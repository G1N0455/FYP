# intraday_mean_reversion_strategy.py
import pandas as pd
import numpy as np
from typing import Literal

class IntradayMeanReversionStrategy:
    """
    改进的日内均值回归策略 (Improved Intraday Mean Reversion Strategy)
    
    High-frequency strategy that trades mean reversion with better entry/exit logic.
    
    Logic:
    1. Use multiple timeframes for confirmation
    2. Better entry conditions with RSI confirmation
    3. Dynamic profit targets and stop losses
    4. Time-based filtering to avoid bad periods
    """
    
    def __init__(self,
                 period: int = 14,
                 rsi_period: int = 14,
                 std_multiplier: float = 1.5,
                 rsi_oversold: int = 30,
                 rsi_overbought: int = 70,
                 profit_target_pct: float = 0.008,    # 0.8%
                 stop_loss_pct: float = 0.004,        # 0.4%
                 max_positions_per_day: int = 3):
        
        self.period = period
        self.rsi_period = rsi_period
        self.std_multiplier = std_multiplier
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_positions_per_day = max_positions_per_day
        
        # State variables
        self.in_position = False
        self.entry_price = 0.0
        self.position_type = 0  # 1 for long, -1 for short
        self.positions_today = 0
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
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
        
        # Calculate indicators
        df['MA'] = df['Close'].rolling(self.period).mean()
        df['STD'] = df['Close'].rolling(self.period).std()
        df['Upper'] = df['MA'] + (df['STD'] * self.std_multiplier)
        df['Lower'] = df['MA'] - (df['STD'] * self.std_multiplier)
        df['RSI'] = self.calculate_rsi(df['Close'], self.rsi_period)
        
        # Time filters - avoid first 30 min and last 30 min of trading
        df['Hour'] = df.index.hour
        df['Minute'] = df.index.minute
        df['TimeFilter'] = True
        # Avoid first 30 minutes (9:30-10:00 ET)
        df.loc[(df['Hour'] == 13) & (df['Minute'] >= 30) & (df['Minute'] <= 59), 'TimeFilter'] = False
        df.loc[(df['Hour'] == 14) & (df['Minute'] <= 0), 'TimeFilter'] = False
        # Avoid last 30 minutes (3:30-4:00 ET)  
        df.loc[(df['Hour'] == 20) & (df['Minute'] >= 30), 'TimeFilter'] = False
        
        # Identify market open for each trading day
        df['Date'] = df.index.date
        
        # Group by date and process each day
        for date, day_data in df.groupby('Date'):
            # Reset daily position counter
            self.positions_today = 0
            
            # Get indices for this day
            day_indices = day_data.index
            
            if len(day_indices) < max(self.period, self.rsi_period):
                continue  # Skip if not enough data
            
            # Process each bar of the day
            for i, idx in enumerate(day_indices):
                current_bar = df.loc[idx]
                
                # Skip if indicators are NaN or time filter
                if (pd.isna(current_bar['MA']) or pd.isna(current_bar['RSI']) or 
                    pd.isna(current_bar['Upper']) or not current_bar['TimeFilter']):
                    continue
                
                # Handle existing positions
                if self.in_position:
                    # Check exit conditions
                    if self.position_type == 1:  # Long position
                        # Stop loss
                        if current_bar['Low'] <= self.entry_price * (1 - self.stop_loss_pct):
                            df.loc[idx, 'Signal'] = -1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                        # Profit target
                        elif current_bar['High'] >= self.entry_price * (1 + self.profit_target_pct):
                            df.loc[idx, 'Signal'] = -1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                        # Mean reversion - price back towards middle
                        elif current_bar['Close'] <= current_bar['MA']:
                            df.loc[idx, 'Signal'] = -1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                    elif self.position_type == -1:  # Short position
                        # Stop loss
                        if current_bar['High'] >= self.entry_price * (1 + self.stop_loss_pct):
                            df.loc[idx, 'Signal'] = 1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                        # Profit target
                        elif current_bar['Low'] <= self.entry_price * (1 - self.profit_target_pct):
                            df.loc[idx, 'Signal'] = 1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                        # Mean reversion - price back towards middle
                        elif current_bar['Close'] >= current_bar['MA']:
                            df.loc[idx, 'Signal'] = 1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                else:
                    # Check entry conditions - only if we haven't hit daily limit
                    if self.positions_today < self.max_positions_per_day:
                        # Buy signal - oversold conditions
                        if (current_bar['Close'] <= current_bar['Lower'] and 
                            current_bar['RSI'] <= self.rsi_oversold and
                            current_bar['Close'] > current_bar['Lower'] * 0.995):  # Not too deep
                            
                            df.loc[idx, 'Signal'] = 1
                            self.in_position = True
                            self.entry_price = current_bar['Close']
                            self.position_type = 1
                            self.positions_today += 1
                        
                        # Sell signal - overbought conditions (for completeness)
                        elif (current_bar['Close'] >= current_bar['Upper'] and 
                              current_bar['RSI'] >= self.rsi_overbought and
                              current_bar['Close'] < current_bar['Upper'] * 1.005):  # Not too high
                            
                            df.loc[idx, 'Signal'] = -1
                            self.in_position = True
                            self.entry_price = current_bar['Close']
                            self.position_type = -1
                            self.positions_today += 1
            
            # Close any open positions at end of day
            if self.in_position and len(day_indices) > 0:
                last_idx = day_indices[-1]
                if df.loc[last_idx, 'Signal'] == 0:  # Only if not already closed
                    df.loc[last_idx, 'Signal'] = -1 if self.position_type == 1 else 1
                self.in_position = False
                self.entry_price = 0.0
                self.position_type = 0
        
        # Clean up temporary columns
        df.drop(['Date', 'Hour', 'Minute', 'TimeFilter', 'MA', 'STD', 'Upper', 'Lower', 'RSI'], 
                axis=1, inplace=True, errors='ignore')
        
        return df
    
    def get_strategy_name(self) -> str:
        """Return strategy name"""
        return f"IntradayMeanReversion_Improved"
    
    def get_parameters(self) -> dict:
        """Return strategy parameters"""
        return {
            'period': self.period,
            'rsi_period': self.rsi_period,
            'std_multiplier': self.std_multiplier,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'profit_target_pct': self.profit_target_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'max_positions_per_day': self.max_positions_per_day
        }