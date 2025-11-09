# csv_data_loader.py
import pandas as pd
from pathlib import Path

class CSVDataLoader:
    """加载本地1分钟CSV数据"""
    
    @staticmethod
    def load_1m_data(file_path: str | Path) -> pd.DataFrame:
        """
        加载1分钟数据
        """
        # Skip first 2 rows (Ticker and Datetime label rows)
        df = pd.read_csv(file_path, skiprows=[0, 1])
        df.columns = ['Datetime', 'Close', 'High', 'Low', 'Open', 'Volume']
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
        
        # Convert to numeric
        for col in ['Close', 'High', 'Low', 'Open', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Create bid/ask with 0.01% spread
        spread = 0.0001
        df['bid'] = df['Close'] * (1 - spread)
        df['ask'] = df['Close'] * (1 + spread)
        df['volume'] = df['Volume']
        
        # Clean and validate
        df.dropna(inplace=True)
        df.sort_index(inplace=True)
        
        if df.empty:
            raise ValueError("DataFrame is empty")
            
        return df
    
    @staticmethod
    def extract_metadata(file_path: str | Path) -> tuple[str, str]:
        """从文件名提取股票代码和时间间隔"""
        filename = Path(file_path).stem
        parts = filename.split('_')
        ticker = parts[0]
        interval = parts[1] if len(parts) > 1 else '1m'
        return ticker, interval

# Simple test
if __name__ == "__main__":
    test_file = Path(r"E:\school\4998\crawler\stock\AAPL_1m_20251107.csv")
    if test_file.exists():
        df = CSVDataLoader.load_1m_data(test_file)
        print(f"Loaded {len(df)} rows")
        print(f"Columns: {df.columns.tolist()}")
        print(df.head())
    else:
        print(f"File not found: {test_file}")