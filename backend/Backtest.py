
from backtesting import Strategy
import pandas as pd


def bbband(close, window=20, num_std=2):
    close = pd.Series(close)
    sma = close.rolling(window).mean()
    std = close.rolling(window).std() 
    
    upper = sma + (num_std * std)
    lower = sma - (num_std * std)
    return upper.values, sma.values, lower.values

class bollinger_band(Strategy):
    def init(self):
        
        self.bb_upper, self.middle, self.lower = self.I(bbband, self.data.Close)
        
    def next(self):
        price = self.data.Close[-1]
        
        # Entry Logic: Buy when price dips below the lower band
        if price < self.lower[-1] and not self.position:
            self.buy()
            
        # Exit Logic: Close the buy position when price returns to the middle (SMA)
        elif price > self.middle[-1] and self.position:
            self.position.close()