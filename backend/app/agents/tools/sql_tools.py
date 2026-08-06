from typing import Annotated, Any

from sqlalchemy import text
from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from app.core.security import pii_masker

from ..db import db
from ..schemas.tool_io import SQLQueryInput, SQLQueryOutput

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
    message_key: Annotated[str, InjectedState("message_key")],
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
    if ":patient_id" not in query:
        return (
            "Error executing query: this query does not filter by :patient_id. "
            "Every query must scope rows to the current patient using the "
            ":patient_id placeholder — rewrite the query and try again."
        )

    merged = {**(parameters or {}), "patient_id": patient_id}
    try:
        with db._engine.connect() as conn:
            result = conn.execute(text(query), merged)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

        if "ma_bn_an" in columns:
            rows = [row for row in rows if row.get("ma_bn_an") == patient_id]

        pii_masker.mask(message_key, rows)
        return SQLQueryOutput(source_columns=columns, data={"rows": rows})
    except Exception as e:
        return f"Error executing query: {str(e)}. Please correct your SQL syntax and try again."

sql_tools = [list_tables, get_table_schema, run_sql_query]
