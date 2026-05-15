import pandas as pd
import chromadb
from openai import OpenAI

def row_to_text(row) -> str:
    # what actually gets embedded — keep it information-dense
    return f"{row['date']} | {row['category']} | {row['title']} | {row.get('value','')} | {row.get('note','')}"

def ingest(csv_path: str, chroma_path: str):
    df = pd.read_csv(csv_path)
    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_or_create_collection("patient_records")
    oai = OpenAI()

    for _, row in df.iterrows():
        text = row_to_text(row)
        emb = oai.embeddings.create(input=text, model="text-embedding-3-small").data[0].embedding
        col.upsert(
            ids=[f"{row['patient_id']}_{row['date']}_{row['category']}"],
            embeddings=[emb],
            documents=[text],
            metadatas=[{
                "patient_id": row["patient_id"],
                "date":       row["date"],
                "category":   row["category"],
            }]
        )
    print(f"Ingested {len(df)} records")

if __name__ == "__main__":
    ingest("data/sample.csv", "./chroma_data")