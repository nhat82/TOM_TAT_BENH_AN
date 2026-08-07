import logging
from langchain_community.utilities import SQLDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

_agent_url = settings.agent_db_url.get_secret_value() if settings.agent_db_url else ""
if not _agent_url:
    _agent_url = settings.db_url.get_secret_value()
    logger.warning(
        "AGENT_DB_URL is not set: the agent's SQL tools are running on the "
        "full-privilege application connection. Set AGENT_DB_URL to the "
        "read-only role before deploying."
    )

# view_support=True: the read-only role only sees views, and SQLDatabase skips
# views during reflection unless asked, which would leave list_tables() empty.
db = SQLDatabase.from_uri(
    _agent_url,
    max_string_length=settings.max_output_string_length,
    sample_rows_in_table_info=0,
    view_support=True,
)

# print(f"Database's table names: {db.get_usable_table_names()}")
