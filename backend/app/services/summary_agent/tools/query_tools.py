"""
Tool to create, call postgresql queries
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from langchain_core.tools import tool
from app.services.database import db
from typing import Optional

@tool
def list_tables() -> str:
    """Returns a comma-separated list of available tables in the database."""
    return ", ".join(db.get_usable_table_names())

@tool
def get_table_schema(table_names: str) -> str:
    """
    Input is a comma-separated string of table names. 
    Returns the schema and sample rows for those tables so you know column names and types.
    """
    return db.get_table_info(table_names=[t.strip() for t in table_names.split(",")])

@tool
def execute_sql_query(query: str, parameters: Optional[dict] = None) -> str:
    """
    Executes a parameterized SQL query against the local database.

    Write the query using named placeholders (e.g. :patient_id, :name)
    and pass the actual values in the `parameters` dict. Never inline
    user-provided values directly into the SQL string.
    
    Example:
        query = "SELECT * FROM visits WHERE patient_id = :patient_id AND status = :status"
        parameters = {"patient_id": 42, "status": "active"}
    """
    try:
        return str(db.run(query, parameters=parameters or {}))
    except Exception as e:
        return f"Error executing query: {str(e)}. Please correct your SQL syntax and try again."

tools = [list_tables, get_table_schema, execute_sql_query]
