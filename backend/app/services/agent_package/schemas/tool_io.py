from pydantic import BaseModel
from typing import Any

class SQLQueryInput(BaseModel): 
    parameters: dict[str, Any] = {}
    query: str
    
class SQLQueryOutput(BaseModel): 
    source_columns: list[str]
    data: dict