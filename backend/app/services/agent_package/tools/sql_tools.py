from typing import Annotated, Any
from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy import text
from ..schemas.tool_io import SQLQueryInput, SQLQueryOutput
from ..db import db

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

@tool(args_schema=SQLQueryInput)
def run_sql_query(
    query: str,
    parameters: dict[str, Any],
    patient_id: Annotated[str, InjectedState("patient_id")],
) -> SQLQueryOutput:
    """
    Executes a parameterized SQL query against the local database.

    Write the query using named placeholders (e.g. :patient_id, :name)
    and pass the actual values in the `parameters` dict. Never inline
    user-provided values directly into the SQL string.
    The current patient's ID is automatically available as :patient_id.

    Example:
        query = "SELECT diagnosis FROM visits WHERE patient_id = :patient_id"
        parameters = {'patient_id': 'BN41'}
    """
    merged = {"patient_id": patient_id, **(parameters or {})}
    try:
        with db._engine.connect() as conn:
            result = conn.execute(text(query), merged)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return SQLQueryOutput(source_columns=columns, data={"rows": rows})
    except Exception as e:
        return f"Error executing query: {str(e)}. Please correct your SQL syntax and try again."

sql_tools = [list_tables, get_table_schema, run_sql_query]
