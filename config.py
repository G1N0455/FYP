# config.py
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

@dataclass
class PathConfig:
    """路径配置"""
    csv_file: Path = Path(r"E:\school\4998\crawler\stock\AAPL_1m_20251107.csv")
    output_folder: Path = Path(r"E:\school\4998\backtesting\test")
    
    def __post_init__(self):
        """确保输出文件夹存在"""
        self.output_folder.mkdir(parents=True, exist_ok=True)

@dataclass
class DataConfig:
    """数据配置"""
    timeframe: str = '15min'  # 15min, 30min, 1h, etc.
    
@dataclass
class StrategyConfig:
    """策略配置"""
    buy_threshold: float = 0.95  # 5% drop
    sell_threshold: float = 1.05  # 5% gain
    # 用于双均线策略参数
    sma_short: int = 5
    sma_long: int = 20
    
@dataclass
class OrderConfig:
    """订单配置"""
    slippage_pct: float = 0.001  # 0.1% slippage
    partial_fill_prob: float = 0.0  # 部分成交概率 (0-1)
    
@dataclass
class PositionConfig:
    """仓位配置"""
    position_type: Literal['fixed_shares', 'fixed_capital'] = 'fixed_capital'
    fixed_shares: int = 100  # 固定股数
    capital_pct: float = 0.95  # 固定资金百分比
    initial_capital: float = 100000.0  # 初始资金
    
@dataclass
class CostConfig:
    """成本配置"""
    commission_type: Literal['fixed', 'percentage'] = 'percentage'
    commission_fixed: float = 0.0  # 固定手续费
    commission_pct: float = 0.001  # 万分之一
    
@dataclass
class ChartConfig:
    """图表配置"""
    dpi: int = 200
    volume: bool = True
    style_up_color: str = 'g'
    style_down_color: str = 'r'
    buy_marker_offset: float = 0.98
    sell_marker_offset: float = 1.02

@dataclass
class BacktestConfig:
    """回测总配置"""
    path: PathConfig = field(default_factory=PathConfig)
    data: DataConfig = field(default_factory=DataConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    order: OrderConfig = field(default_factory=OrderConfig)
    position: PositionConfig = field(default_factory=PositionConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    chart: ChartConfig = field(default_factory=ChartConfig)