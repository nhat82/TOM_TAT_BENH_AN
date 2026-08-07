from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from app.core.config import settings

engine = create_engine(settings.db_url.get_secret_value())

db = SQLDatabase.from_uri(
    settings.db_url.get_secret_value(),
    max_string_length=settings.max_output_string_length,
    sample_rows_in_table_info=0,
)
