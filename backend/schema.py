from pydantic import BaseModel
from datetime import datetime


class Symbol(BaseModel):
    syk:str
    


class Data(BaseModel):
    Symbol:str
    Date:datetime
    Open:float
    High:float
    Close:float
    Volume:float
    Return:float
    
class BacktestRequest(BaseModel):
    investement: float
    sym: str
    stra: str