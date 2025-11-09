# performance_analyzer.py
import pandas as pd
import numpy as np

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.equity_curve = []
    
    def update_equity(self, timestamp: pd.Timestamp, equity: float):
        """更新权益曲线"""
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity,
            'returns': (equity / self.initial_capital - 1) if self.initial_capital > 0 else 0
        })
    
    def calculate_metrics(self, trades_df: pd.DataFrame) -> dict:
        """计算关键指标"""
        if self.equity_curve:
            equity_df = pd.DataFrame(self.equity_curve)
            equity_df.set_index('timestamp', inplace=True)
        else:
            return {}
        
        # 总回报
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity / self.initial_capital - 1) * 100
        
        # 年化回报（假设252个交易日）
        days = (equity_df.index[-1] - equity_df.index[0]).days
        years = days / 252 if days > 0 else 1
        annual_return = ((final_equity / self.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0
        
        # 最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak']
        max_drawdown = equity_df['drawdown'].min() * 100
        
        # Sharpe Ratio（假设无风险利率=0）
        returns = equity_df['returns'].pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0 and negative_returns.std() > 0:
            sortino_ratio = returns.mean() / negative_returns.std() * np.sqrt(252)
        else:
            sortino_ratio = 0
        
        # 交易统计
        if not trades_df.empty and 'net_pnl' in trades_df.columns:
            closed_trades = trades_df[trades_df['signal_type'] == 'SELL']
            if not closed_trades.empty:
                winning_trades = closed_trades[closed_trades['net_pnl'] > 0]
                win_rate = len(winning_trades) / len(closed_trades) * 100
                
                avg_win = winning_trades['net_pnl'].mean() if len(winning_trades) > 0 else 0
                avg_loss = abs(closed_trades[closed_trades['net_pnl'] < 0]['net_pnl'].mean()) if len(closed_trades[closed_trades['net_pnl'] < 0]) > 0 else 1
                profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            else:
                win_rate = 0
                profit_factor = 0
        else:
            win_rate = 0
            profit_factor = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return,
            'annual_return_pct': annual_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            'total_trades': len(trades_df),
            'days': days
        }
    
    def get_equity_df(self) -> pd.DataFrame:
        """获取权益曲线DataFrame"""
        return pd.DataFrame(self.equity_curve)