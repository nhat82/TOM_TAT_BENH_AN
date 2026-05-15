"""
Medical-record ingestion pipeline
==================================
• Synonym expansion - medical abbreviations → canonical Vietnamese
• Word segmentation - underthesea before embedding
• Embedding        - paraphrase-multilingual-mpnet-base-v2
• ChromaDB upsert  - incremental (hash-gated, skips unchanged records)
• Reranker         - BAAI/bge-reranker-v2-m3 at query time

CLI usage
---------
  python -m app.services.ingest ingest [--csv PATH] [--force]
  python -m app.services.ingest query  "ung thư phổi THA" [--top-k 20] [--top-n 5]
  python -m app.services.ingest stats
"""

from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path

import pandas as pd
import regex as re  # Unicode-aware (already in requirements.txt)

# ── paths & constants ─────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).resolve().parent.parent.parent   # backend/
CHROMA_PATH     = BASE_DIR / "data" / "chromadb"
DEFAULT_CSV     = BASE_DIR / "data" / "Sample_20BN.csv"
COLLECTION_NAME = "medical_records"
EMBED_MODEL     = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
RERANK_MODEL    = "BAAI/bge-reranker-v2-m3"
TOP_K_DEFAULT   = 20   # candidates retrieved from ChromaDB before reranking
TOP_N_DEFAULT   = 5    # final results returned after reranking

# ── Medical synonym map ───────────────────────────────────────────────────────
# Longer / more-specific patterns listed first to avoid partial replacements.
_SYNONYM_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r'\bđái tháo đường\b',  re.IGNORECASE), 'Tiểu đường'),
    (re.compile(r'\bu đầu tụy\b',       re.IGNORECASE), 'Khối u tuyến tụy'),
    (re.compile(r'\bĐTĐ\b'),                            'Tiểu đường'),
    (re.compile(r'\bTHA\b'),                            'Tăng huyết áp'),
    # "K" as cancer — guard against "K+" (potassium in lab values) and "K="
    (re.compile(r'\bK\b(?!\s*[+=\d])'),                 'Ung thư'),
    (re.compile(r'\bBN\b'),                             'Bệnh nhân'),
    # "TP" as ingredient/component — skip "TP." (city abbreviation TP.HCM)
    (re.compile(r'\bTP\b(?!\.)'),                       'Thành phần'),
]

# ── Text fields to embed (priority order; empty/NULL fields are skipped) ──────
_TEXT_FIELDS: list[tuple[str, str]] = [
    # Clinical narrative — most semantically rich → first so model truncation
    # keeps the most valuable content within the 128-token window
    ("lydovaovien",                    "LÝ DO VÀO VIỆN"),
    ("quatrinhbenhly",                 "QUÁ TRÌNH BỆNH LÝ"),
    ("tiensubenh",                     "TIỀN SỬ BỆNH"),
    ("tomtatketquacls",                "KẾT QUẢ CLS"),
    ("quatrinhbenhlyvadienbienlamsang","DIỄN BIẾN LÂM SÀNG"),
    ("phuongphapdieutri",              "PHƯƠNG PHÁP ĐIỀU TRỊ"),
    ("pttt",                           "PHẪU THUẬT THỦ THUẬT"),
    ("tinhtrangnguoiravien",           "TÌNH TRẠNG RA VIỆN"),
    ("huongdieutritieptheo",           "HƯỚNG ĐIỀU TRỊ TIẾP THEO"),
    # Diagnoses
    ("lydodenkham",                    "LÝ DO ĐẾN KHÁM"),
    ("chandoantuyenduoi",              "CHẨN ĐOÁN TUYẾN DƯỚI"),
    ("chandoan_in",                    "CHẨN ĐOÁN VÀO VIỆN"),
    ("chandoan_in_kemtheo",            "CHẨN ĐOÁN KÈM THEO"),
    ("chandoan_kb_main",               "CHẨN ĐOÁN KHÁM BỆNH"),
    ("chandoan_kb_ex",                 "CHẨN ĐOÁN KB PHỤ"),
    ("chandoan_out_main",              "CHẨN ĐOÁN RA VIỆN"),
    ("chandoan_out_ex",                "CHẨN ĐOÁN RA VIỆN PHỤ"),
    ("huongdieutri_out",               "HƯỚNG ĐIỀU TRỊ RA VIỆN"),
    # Structured results — truncated so they don't dominate the embedding
    ("ds_xet_nghiem",                  "XÉT NGHIỆM"),
    ("ds_cdha",                        "CHẨN ĐOÁN HÌNH ẢNH"),
    ("ds_thuoc",                       "THUỐC"),
    ("ds_dich_vu",                     "DỊCH VỤ"),
]

# Fields stored as ChromaDB metadata (all values coerced to str)
_META_FIELDS: list[str] = [
    "ma_bn_an", "ho_ten", "dm_gioitinhid", "birthdayyear", "dm_tinhcode",
    "medicalrecorddate_in", "medicalrecorddate_out", "so_ngay_dieu_tri",
    "departmentid", "chandoan_out_main", "chandoan_out_main_icd10",
    "chandoan_in_icd10", "isbn_ut",
]

_NULL_VALUES = {"null", "nan", "none", "", "0", "0.0"}

log = logging.getLogger(__name__)


# ── text helpers ──────────────────────────────────────────────────────────────

def expand_synonyms(text: str) -> str:
    """Expand medical abbreviations to their canonical Vietnamese forms."""
    for pattern, replacement in _SYNONYM_MAP:
        text = pattern.sub(replacement, text)
    return text


def segment_vi(text: str) -> str:
    """Vietnamese word segmentation via underthesea (lazy import)."""
    from underthesea import word_tokenize
    return word_tokenize(text, format="text")


def _is_empty(val: str) -> bool:
    return val.strip().lower() in _NULL_VALUES


def _truncate(text: str, max_chars: int = 600) -> str:
    return text[:max_chars] + "…" if len(text) > max_chars else text


def build_document(row: dict) -> str:
    """Combine patient text fields into one labelled document string."""
    parts: list[str] = []
    for field, label in _TEXT_FIELDS:
        val = str(row.get(field, "")).strip()
        if _is_empty(val):
            continue
        if field in ("ds_xet_nghiem", "ds_cdha", "ds_thuoc", "ds_dich_vu"):
            val = _truncate(val)
        parts.append(f"[{label}] {val}")
    return "\n".join(parts)


def preprocess(text: str) -> str:
    """Expand synonyms then Vietnamese word-segment."""
    return segment_vi(expand_synonyms(text))


def build_metadata(row: dict) -> dict[str, str]:
    meta: dict[str, str] = {}
    for field in _META_FIELDS:
        val = row.get(field, "")
        if val is None or str(val).strip().lower() in _NULL_VALUES:
            val = ""
        meta[field] = str(val)
    return meta


def content_hash(row: dict) -> str:
    """MD5 of the raw document — used to detect changed records."""
    return hashlib.md5(build_document(row).encode()).hexdigest()


# ── lazy model singletons ─────────────────────────────────────────────────────

_embedder = None
_reranker = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        log.info("Loading embedder: %s", EMBED_MODEL)
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def get_reranker():
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker
        log.info("Loading reranker: %s", RERANK_MODEL)
        _reranker = FlagReranker(RERANK_MODEL, use_fp16=True)
    return _reranker


# ── ChromaDB helpers ──────────────────────────────────────────────────────────

def get_collection():
    import chromadb
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ── ingestion ─────────────────────────────────────────────────────────────────

def ingest_csv(csv_path: Path = DEFAULT_CSV, force: bool = False) -> dict:
    """
    Load csv_path, expand synonyms, word-segment, embed, and upsert into
    ChromaDB.  Records whose content hash hasn't changed are skipped unless
    force=True.

    The CSV is expected to have:
      row 0 – column headers
      row 1 – human-readable field descriptions  ← skipped via skiprows=1
      rows 2+ – patient data

    Returns {"added": int, "skipped": int}.
    """
    df = pd.read_csv(csv_path, skiprows=1, dtype=str)
    df.fillna("", inplace=True)

    collection = get_collection()

    # Build map of patient_id → stored hash for change detection
    existing = collection.get(include=["metadatas"])
    existing_hashes: dict[str, str] = {}
    if existing["metadatas"]:
        for meta in existing["metadatas"]:
            pid = meta.get("ma_bn_an", "")
            if pid:
                existing_hashes[pid] = meta.get("_hash", "")

    ids_to_upsert:   list[str]   = []
    docs_to_upsert:  list[str]   = []
    metas_to_upsert: list[dict]  = []
    skipped = 0

    for _, row in df.iterrows():
        record_id = str(row.get("ma_bn_an", "")).strip()
        if not record_id or _is_empty(record_id):
            continue

        chash = content_hash(row)
        if not force and existing_hashes.get(record_id) == chash:
            skipped += 1
            continue

        raw_doc = build_document(row)
        if not raw_doc.strip():
            log.warning("Record %s: no usable text content — skipped.", record_id)
            skipped += 1
            continue

        processed_doc = preprocess(raw_doc)
        meta = build_metadata(row)
        meta["_hash"] = chash

        ids_to_upsert.append(record_id)
        docs_to_upsert.append(processed_doc)
        metas_to_upsert.append(meta)

    if not ids_to_upsert:
        log.info("Nothing new to ingest (%d record(s) unchanged).", skipped)
        return {"added": 0, "skipped": skipped}

    log.info("Embedding %d record(s) …", len(ids_to_upsert))
    embedder = get_embedder()
    embeddings = embedder.encode(
        docs_to_upsert,
        show_progress_bar=True,
        normalize_embeddings=True,
        batch_size=32,
    )

    log.info("Upserting into ChromaDB collection '%s' …", COLLECTION_NAME)
    collection.upsert(
        ids=ids_to_upsert,
        documents=docs_to_upsert,
        embeddings=embeddings.tolist(),
        metadatas=metas_to_upsert,
    )

    log.info("Done — added/updated: %d  unchanged: %d", len(ids_to_upsert), skipped)
    return {"added": len(ids_to_upsert), "skipped": skipped}


# ── query + rerank ────────────────────────────────────────────────────────────

def query(
    query_text: str,
    top_k: int = TOP_K_DEFAULT,
    top_n: int = TOP_N_DEFAULT,
) -> list[dict]:
    """
    Semantic search over the ChromaDB collection with BGE reranking.

    Pipeline:
      expand synonyms → word-segment → embed
      → ChromaDB ANN top_k
      → BGE-Reranker-v2-m3 top_n

    Returns a list of result dicts sorted by rerank_score descending.
    """
    processed_q = preprocess(query_text)

    embedder = get_embedder()
    q_vec = embedder.encode([processed_q], normalize_embeddings=True)[0]

    collection = get_collection()
    n_docs = collection.count()
    if n_docs == 0:
        log.warning("Collection is empty — run `ingest` first.")
        return []

    results = collection.query(
        query_embeddings=[q_vec.tolist()],
        n_results=min(top_k, n_docs),
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    if not docs:
        return []

    reranker = get_reranker()
    scores   = reranker.compute_score([[processed_q, doc] for doc in docs], normalize=True)

    ranked = sorted(
        zip(scores, docs, metas, distances),
        key=lambda x: x[0],
        reverse=True,
    )[:top_n]

    return [
        {
            "rerank_score":    round(float(score), 4),
            "cosine_distance": round(float(dist),  4),
            "patient_id":      meta.get("ma_bn_an", ""),
            "metadata":        meta,
            "document":        doc,
        }
        for score, doc, meta, dist in ranked
    ]


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m app.services.ingest",
        description="Medical record ChromaDB pipeline",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="Ingest CSV into ChromaDB")
    pi.add_argument(
        "--csv", type=Path, default=DEFAULT_CSV,
        metavar="PATH",
        help=f"CSV file to ingest (default: {DEFAULT_CSV.name})",
    )
    pi.add_argument(
        "--force", action="store_true",
        help="Re-embed all records even if content is unchanged",
    )

    pq = sub.add_parser("query", help="Semantic search with reranking")
    pq.add_argument("text", nargs="+", help="Query text (Vietnamese or abbreviations ok)")
    pq.add_argument("--top-k", type=int, default=TOP_K_DEFAULT,
                    help="Candidates fetched from ChromaDB before reranking")
    pq.add_argument("--top-n", type=int, default=TOP_N_DEFAULT,
                    help="Final results after reranking")

    sub.add_parser("stats", help="Show collection statistics")

    return p


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args = _build_parser().parse_args()

    if args.cmd == "ingest":
        result = ingest_csv(args.csv, force=args.force)
        print(f"\nIngest complete: {result}")

    elif args.cmd == "query":
        text = " ".join(args.text)
        print(f"\nQuerying: «{text}»\n{'─' * 60}")
        hits = query(text, top_k=args.top_k, top_n=args.top_n)
        if not hits:
            print("No results.")
            return
        for i, hit in enumerate(hits, 1):
            print(
                f"\n[{i}] {hit['patient_id']}"
                f"  rerank={hit['rerank_score']:.4f}"
                f"  cosine_dist={hit['cosine_distance']:.4f}"
            )
            preview = hit["document"].replace("\n", " | ")[:400]
            print(f"    {preview}")

    elif args.cmd == "stats":
        col = get_collection()
        print(f"Collection '{COLLECTION_NAME}': {col.count()} document(s)")
        print(f"ChromaDB path: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
