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






app=FastAPI()

app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173"], 
                   allow_credentials=True,
                   allow_methods=["*"], 
                   allow_headers=["*"],)
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
def test_bollinger(data:BacktestRequest, db: Session = Depends(get_db)
                   ):
    symbol1 =data.sym.upper()
    query = text(
        'SELECT "symbol","date","open","high","low","close","volume" '
        'FROM hydropower WHERE "symbol" = :symbol ORDER BY "date"'
    )
    result = db.execute(query, {"symbol": symbol1}).fetchall()
    
    if not result:
        return {"status": "fail"}

    df = pd.DataFrame(result, columns=['Symbol','Date','Open','High','Low','Close','Volume'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    for col in ['Close', 'Open', 'High', 'Low', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    inital_investment2 = data.investement
    strategy_select=None
    if data.stra=="Bollinger Band":
        strategy_select=bollinger_band
    bt = Backtest(df, strategy_select, cash=inital_investment2, commission=0)
    stats = bt.run()

    raw_response = {
        "ohlc": df.reset_index().to_dict(orient="records"),
        "bb": {
            "upper": stats._strategy.bb_upper.tolist(),
            "middle": stats._strategy.middle.tolist(),
            "lower": stats._strategy.lower.tolist()
        },
        "trades": stats._trades.to_dict(orient="records")
    }

    return jsonable_encoder(deep_sanitize(raw_response))