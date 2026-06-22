from langchain_community.utilities import SQLDatabase
from app.config import settings

db = SQLDatabase.from_uri(
    settings.db_url.get_secret_value(), 
    max_string_length = settings.max_output_string_length, 
    sample_rows_in_table_info=0
)

# print(f"Database's table names: {db.get_usable_table_names()}")