from typing import Annotated, Any
from langchain.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy import text
from ..schemas.tool_io import SQLQueryInput, SQLQueryOutput
from ..db import db
from ..masking import mask_rows

@tool
def list_tables() -> str:
    """Returns a comma-separated list of available tables in the database."""
    tables = db.get_usable_table_names()
    return ", ".join(tables)

@tool
def get_table_schema(table_names: str) -> str:
    """
    Input is a comma-separated string of table names.
    Returns the schema and sample rows for those tables so you know column names and types.
    """
    requested = [t.strip() for t in table_names.split(",")]
    return db.get_table_info(table_names=requested)

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
    The current patient's ID is automatically available as :patient_id — do
    NOT put "patient_id" in `parameters` yourself, it is injected and any
    value you pass there is ignored. In table ai_benh_an_so this corresponds
    to the column `ma_bn_an` (a string code, e.g. "BA2025000006") — NOT the
    `id` column, which is an unrelated bigint primary key. Always confirm the
    correct join/filter column via get_table_schema before writing the query.

    Personal-identity columns (ho_ten, cccd, isbn_ut, birthdayyear,
    dm_tinhcode) are returned masked as numbered placeholders such as
    "[ho_ten_1]", "[cccd_1]" — one number per distinct real value. Keep the
    placeholders verbatim in your answer; they are restored for the user.
    Select those columns under their original name (no alias).

    Example:
        query = "SELECT diagnosis FROM visits WHERE patient_id = :patient_id"
        parameters = {'patient_id': 'BN41'}
    """
    merged = {**(parameters or {}), "patient_id": patient_id}
    try:
        with db._engine.connect() as conn:
            result = conn.execute(text(query), merged)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
        masked = mask_rows(rows)
        return SQLQueryOutput(source_columns=columns, data={"rows": masked})
    except Exception as e:
        return f"Error executing query: {str(e)}. Please correct your SQL syntax and try again."

sql_tools = [list_tables, get_table_schema, run_sql_query]
