from fastapi import FastAPI,Depends
from db import Sessionlocal
from schema import Symbol
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
from schema import Data
from Backtest import bollinger_band
from backtesting import Backtest
import numpy as np
import math
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from schema import BacktestRequest
from Backtest import macrossover,MeanReversion







app=FastAPI()

origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             
    allow_credentials=True,
    allow_methods=["*"],               
    allow_headers=["*"],               
)
def get_db():
    db=Sessionlocal()
    try:
        yield db
    finally:
        db.close()
        

 
@app.get("/")
def root():
    return {"message": "API is running"}



@app.get('/hydroname')
def get_hydro_name(db:Session=Depends(get_db)):
    query=text('SELECT "symbol" FROM hydropower  GROUP BY "symbol"')
    result=db.execute(query).fetchall()
    if not result:
        return {"status":"fail","message":"no data found"}
    
    df=pd.DataFrame(result,columns=['Symbol'])
    return df.to_dict(orient="records")
       
        
@app.post("/gethydro")
def get_hydro_data(sym:str,db:Session=Depends(get_db)):
    symbol=sym.upper()
    query=text('SELECT * FROM hydropower WHERE "symbol" = :symbol ORDER BY "date"')
    result=db.execute(query,{"symbol":symbol}).fetchall()
    if  not result:
       return {"status": "fail", "message": "No data found"}
   
    df=pd.DataFrame(result,columns=['Symbol','Date','Open','High','low','Close','Volume','Return'])
    return df.to_dict(orient="records")
   

def deep_sanitize(obj):
    if isinstance(obj, dict):
        return {k: deep_sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
    
        return [deep_sanitize(i) for i in obj]
    elif isinstance(obj, (float, np.floating)):
        return float(obj) if math.isfinite(obj) else None
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    return obj

@app.post("/bbband")
def test_bollinger(data: BacktestRequest, db: Session = Depends(get_db)):
    symbol1 = data.sym.upper()
    

    query = text(
        'SELECT "date", "open", "high", "low", "close", "volume" '
        'FROM hydropower WHERE "symbol" = :symbol ORDER BY "date"'
    )
    result = db.execute(query, {"symbol": symbol1}).fetchall()
    
    if not result:
        return {"status": "fail", "message": "No data found for symbol"}

    df = pd.DataFrame(result, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = \
    df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    

    

    strategies = {
        "Bollinger Band": bollinger_band,
        "Moving Average Crossover": macrossover,
        "Mean Reversion": MeanReversion
    }
    
    strategy_select = strategies.get(data.stra)
    if not strategy_select:
        return {"status": "fail", "message": "Invalid strategy selected"}

    bt = Backtest(df, strategy_select, cash=data.investement, commission=0)
    stats = bt.run()
    trades_list = []
    if '_trades' in stats and not stats['_trades'].empty:
    
             df_trades = stats['_trades'].copy()
    

             df_trades['EntryTime'] = df_trades['EntryTime'].dt.strftime('%Y-%m-%d')
             df_trades['ExitTime'] = df_trades['ExitTime'].dt.strftime('%Y-%m-%d')
    
    
             trades_list = df_trades.to_dict(orient='records')
    
    ohlc_data = []
    for index, row in df.iterrows():
        ohlc_data.append({
            "time": index.strftime('%Y-%m-%d'),
            "open": row['Open'],
            "high": row['High'],
            "low": row['Low'],
            "close": row['Close'],
        })

    
    raw_response = {
        "summary": {
            "Start Cash": data.investement,
            "Final Equity": stats['Equity Final [$]'],
            "Return [%]": stats['Return [%]'],
            "Buy & Hold Return [%]": stats['Buy & Hold Return [%]'],
            "Max Drawdown [%]": stats['Max. Drawdown [%]'],
            "Total Trades": stats['# Trades'],
            "Win Rate [%]": stats['Win Rate [%]'],
            "Sharpe Ratio": float(stats['Sharpe Ratio']),
        },
        "ohlc": ohlc_data,
        "trades": trades_list
    }


    if data.stra == "Bollinger Band":
        raw_response["indicators"] = {
            "upper": stats['_strategy'].bb_upper.tolist(),
            "middle": stats['_strategy'].middle.tolist(),
            "lower": stats['_strategy'].lower.tolist()
        }
    elif data.stra == "Ma crossover":
        raw_response["indicators"] = {
            "fast_ma": stats['_strategy'].fast.tolist(),
            "slow_ma": stats['_strategy'].slow.tolist()
        }
    elif data.stra == "Mean Reversion":
        raw_response["indicators"] = {
            "zscore": stats['_strategy'].zscore.tolist()
        }

    return jsonable_encoder(deep_sanitize(raw_response))