
from backtesting import Strategy
import pandas as pd
import numpy as np

def bbband(close, window=20, num_std=2):
    close = pd.Series(close)
    sma = close.rolling(window).mean()
    std = close.rolling(window).std() 
    
    upper = sma + (num_std * std)
    lower = sma - (num_std * std)
    return upper.values, sma.values, lower.values

def ma(close, fast=10, slow=25):
    close = np.asarray(close, dtype=float)

    fast_ma = np.full(len(close), np.nan)
    slow_ma = np.full(len(close), np.nan)

    for i in range(fast, len(close)):
        fast_ma[i] = close[i-fast:i].mean()

    for i in range(slow, len(close)):
        slow_ma[i] = close[i-slow:i].mean()

    return fast_ma, slow_ma

def mean_reversion(close, window=20):
    close = np.asarray(close, dtype=float)

    z = np.full(len(close), np.nan)

    for i in range(window, len(close)):
        mean = close[i-window:i].mean()
        std = close[i-window:i].std()

        if std != 0:
            z[i] = (close[i] - mean) / std

    return z



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
            
            
class macrossover(Strategy):
    def init(self):
        self.fast,self.slow=self.I(ma,self.data.Close)
        
    def next(self):
        if self.fast[-1]>self.slow[-1] and not self.position:
            self.buy()
            
        elif self.fast[-1]<self.slow[-1] and not self.position:
            self.position.close()
        

class MeanReversion(Strategy):
    z_entry = 1.95
    
    def init(self):
        
        self.zscore = self.I(mean_reversion, self.data.Close)
        
    def next(self):
    
        if self.zscore[-1] < -self.z_entry and not self.position:
            self.buy()
        
        elif self.zscore[-1] > 0 and self.position:
            self.position.close()