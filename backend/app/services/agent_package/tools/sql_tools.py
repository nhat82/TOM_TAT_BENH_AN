from typing import Annotated, Any
from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy import text
from ..schemas.tool_io import SQLQueryInput, SQLQueryOutput
from ..db import db
from ..masking import mask_rows
from ..audit import (
    log_sql_query,
    log_sql_rows,
    log_tool_call,
    log_tool_error,
    log_tool_result,
)

@tool
def list_tables() -> str:
    """Returns a comma-separated list of available tables in the database."""
    started = log_tool_call("list_tables")
    try:
        tables = db.get_usable_table_names()
    except Exception as e:
        log_tool_error("list_tables", started, e)
        raise
    log_tool_result("list_tables", started, table_count=len(list(tables)))
    return ", ".join(tables)

@tool
def get_table_schema(table_names: str) -> str:
    """
    Input is a comma-separated string of table names.
    Returns the schema and sample rows for those tables so you know column names and types.
    """
    requested = [t.strip() for t in table_names.split(",")]
    started = log_tool_call("get_table_schema", table_names=requested)
    try:
        info = db.get_table_info(table_names=requested)
    except Exception as e:
        log_tool_error("get_table_schema", started, e)
        raise
    log_tool_result("get_table_schema", started, schema_length=len(info))
    return info

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

    Personal-identity columns (ho_ten, cccd, isbn_ut, birthdayyear,
    dm_tinhcode) are returned masked as numbered placeholders such as
    "[ho_ten_1]", "[cccd_1]" — one number per distinct real value. Keep the
    placeholders verbatim in your answer; they are restored for the user.
    Select those columns under their original name (no alias).

    Example:
        query = "SELECT diagnosis FROM visits WHERE patient_id = :patient_id"
        parameters = {'patient_id': 'BN41'}
    """
    merged = {"patient_id": patient_id, **(parameters or {})}
    started = log_tool_call("run_sql_query", patient_id=patient_id)
    # Records the statement and flags anything beyond a plain read (WARNING).
    verdict = log_sql_query(query, merged)
    try:
        with db._engine.connect() as conn:
            result = conn.execute(text(query), merged)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        masked = mask_rows(rows)
        log_sql_rows(columns, masked)
        log_tool_result(
            "run_sql_query",
            started,
            row_count=len(rows),
            read_only=verdict["read_only"],
        )
        return SQLQueryOutput(source_columns=columns, data={"rows": masked})
    except Exception as e:
        log_tool_error("run_sql_query", started, e, read_only=verdict["read_only"])
        return f"Error executing query: {str(e)}. Please correct your SQL syntax and try again."

sql_tools = [list_tables, get_table_schema, run_sql_query]
