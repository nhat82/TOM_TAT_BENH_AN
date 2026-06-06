from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
import os 

load_dotenv()

pg_uri = os.getenv("PG_URI")
MAX_OUTPUT_STRING_LENGTH = 999999999
db = SQLDatabase.from_uri(pg_uri, max_string_length=MAX_OUTPUT_STRING_LENGTH)



print(f"Database's table names: {db.get_usable_table_names()}")