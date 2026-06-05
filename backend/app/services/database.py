from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv
import os 

load_dotenv()

pg_uri = os.getenv("PG_URI")
db = SQLDatabase.from_uri(pg_uri)

print(f"Database's table names: {db.get_usable_table_names()}")