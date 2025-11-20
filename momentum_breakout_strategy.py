# momentum_breakout_strategy.py
import pandas as pd
import numpy as np

class MomentumBreakoutStrategy:
    """
    动量突破策略 (Momentum Breakout Strategy)
    
    High-frequency momentum strategy that trades breakouts with volume confirmation.
    
    Logic:
    1. Calculate price momentum over lookback period
    2. Confirm with volume surge
    3. BUY on strong upward momentum with volume
    4. SELL on strong downward momentum or profit target/stop loss
    
    Parameters:
    - lookback_period: Period to calculate momentum (default: 10)
    - momentum_threshold: Minimum momentum to trigger signal (default: 0.3%)
    - volume_multiplier: Volume surge threshold (default: 1.5x)
    - profit_target_pct: Take profit % (default: 0.8%)
    - stop_loss_pct: Stop loss % (default: 0.4%)
    """
    
    def __init__(self,
                 lookback_period: int = 10,
                 momentum_threshold: float = 0.003,   # 0.3%
                 volume_multiplier: float = 1.5,
                 profit_target_pct: float = 0.008,     # 0.8%
                 stop_loss_pct: float = 0.004):        # 0.4%
        
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
        self.volume_multiplier = volume_multiplier
        self.profit_target_pct = profit_target_pct
        self.stop_loss_pct = stop_loss_pct
        
        # State variables
        self.in_position = False
        self.entry_price = 0.0
        self.position_type = 0  # 1 for long, -1 for short
    
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
        
        # Calculate momentum
        df['Price_Lookback'] = df['Close'].shift(self.lookback_period)
        df['Momentum'] = (df['Close'] - df['Price_Lookback']) / df['Price_Lookback']
        
        # Calculate average volume
        df['Avg_Volume'] = df['Volume'].rolling(window=20, min_periods=1).mean()
        
        # Time filters - avoid first 15 min and last 15 min of trading
        df['Hour'] = df.index.hour
        df['Minute'] = df.index.minute
        df['TimeFilter'] = True
        # Avoid first 15 minutes (9:30-9:45 ET)
        df.loc[(df['Hour'] == 13) & (df['Minute'] >= 30) & (df['Minute'] <= 44), 'TimeFilter'] = False
        # Avoid last 15 minutes (3:45-4:00 ET)  
        df.loc[(df['Hour'] == 20) & (df['Minute'] >= 45), 'TimeFilter'] = False
        
        # Identify market open for each trading day
        df['Date'] = df.index.date
        
        # Group by date and process each day
        for date, day_data in df.groupby('Date'):
            # Get indices for this day
            day_indices = day_data.index
            
            if len(day_indices) < self.lookback_period + 5:
                continue  # Skip if not enough data
            
            # Process each bar of the day
            for i, idx in enumerate(day_indices):
                current_bar = df.loc[idx]
                
                # Skip if indicators are NaN or time filter
                if (pd.isna(current_bar['Momentum']) or pd.isna(current_bar['Avg_Volume']) or 
                    not current_bar['TimeFilter']):
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
                        # Reverse momentum signal
                        elif current_bar['Momentum'] < -self.momentum_threshold:
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
                        # Reverse momentum signal
                        elif current_bar['Momentum'] > self.momentum_threshold:
                            df.loc[idx, 'Signal'] = 1
                            self.in_position = False
                            self.entry_price = 0.0
                            self.position_type = 0
                else:
                    # Check entry conditions
                    volume_surge = current_bar['Volume'] > current_bar['Avg_Volume'] * self.volume_multiplier
                    
                    # Buy signal - strong upward momentum with volume
                    if (current_bar['Momentum'] > self.momentum_threshold and volume_surge):
                        df.loc[idx, 'Signal'] = 1
                        self.in_position = True
                        self.entry_price = current_bar['Close']
                        self.position_type = 1
                    
                    # Sell signal - strong downward momentum with volume
                    elif (current_bar['Momentum'] < -self.momentum_threshold and volume_surge):
                        df.loc[idx, 'Signal'] = -1
                        self.in_position = True
                        self.entry_price = current_bar['Close']
                        self.position_type = -1
            
            # Close any open positions at end of day
            if self.in_position and len(day_indices) > 0:
                last_idx = day_indices[-1]
                if df.loc[last_idx, 'Signal'] == 0:  # Only if not already closed
                    df.loc[last_idx, 'Signal'] = -1 if self.position_type == 1 else 1
                self.in_position = False
                self.entry_price = 0.0
                self.position_type = 0
        
        # Clean up temporary columns
        df.drop(['Date', 'Hour', 'Minute', 'TimeFilter', 'Price_Lookback', 'Momentum', 'Avg_Volume'], 
                axis=1, inplace=True, errors='ignore')
        
        return df
    
    def get_strategy_name(self) -> str:
        """Return strategy name"""
        return f"MomentumBreakout_{self.lookback_period}period"
    
    def get_parameters(self) -> dict:
        """Return strategy parameters"""
        return {
            'lookback_period': self.lookback_period,
            'momentum_threshold': self.momentum_threshold,
            'volume_multiplier': self.volume_multiplier,
            'profit_target_pct': self.profit_target_pct,
            'stop_loss_pct': self.stop_loss_pct
        }