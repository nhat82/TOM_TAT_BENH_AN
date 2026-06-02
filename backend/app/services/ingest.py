"""
Medical-record ingestion pipeline
• Embeds documents with gemini-embedding-2 via Google REST API
• Upserts into ChromaDB (incremental, hash-gated)

CLI:
  python -m app.services.ingest ingest [--csv PATH] [--force]
  python -m app.services.ingest stats
"""
from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path

import pandas as pd

BASE_DIR    = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV = BASE_DIR / "data" / "Sample_20BN.csv"

_TEXT_FIELDS: list[tuple[str, str]] = [
    # Diagnoses
    ("lydodenkham",                     "LÝ DO ĐẾN KHÁM"),
    ("lydovaovien",                     "LÝ DO VÀO VIỆN"),
    ("lydobnvaonoitru",                 "LÝ DO VÀO NỘI TRÚ"),
    ("chandoantuyenduoi",               "CHẨN ĐOÁN TUYẾN DƯỚI"),
    ("chandoantuyenduoi_icd10",         "ICD-10 TUYẾN DƯỚI"),
    ("chandoantuyenduoi_kemtheo",       "CHẨN ĐOÁN TUYẾN DƯỚI KÈM THEO"),
    ("chandoantuyenduoi_kemtheo_icd10", "ICD-10 TUYẾN DƯỚI KÈM THEO"),
    ("chandoan_in",                     "CHẨN ĐOÁN VÀO VIỆN"),
    ("chandoan_in_icd10",               "ICD-10 VÀO VIỆN"),
    ("chandoan_in_kemtheo",             "CHẨN ĐOÁN VÀO VIỆN KÈM THEO"),
    ("chandoan_in_icd10_kemtheo",       "ICD-10 VÀO VIỆN KÈM THEO"),
    ("chandoan_kb_main",                "CHẨN ĐOÁN KHÁM BỆNH"),
    ("chandoan_kb_main_icd10",          "ICD-10 KHÁM BỆNH"),
    ("chandoan_kb_ex",                  "CHẨN ĐOÁN KHÁM BỆNH PHỤ"),
    ("chandoan_kb_ex_icd10",            "ICD-10 KHÁM BỆNH PHỤ"),
    ("chandoan_out_main",               "CHẨN ĐOÁN RA VIỆN"),
    ("chandoan_out_main_icd10",         "ICD-10 RA VIỆN"),
    ("chandoan_out_ex",                 "CHẨN ĐOÁN RA VIỆN PHỤ"),
    ("chandoan_out_ex_icd10",           "ICD-10 RA VIỆN PHỤ"),
    # Clinical narratives
    ("quatrinhbenhly",                  "QUÁ TRÌNH BỆNH LÝ"),
    ("tiensubenh",                      "TIỀN SỬ BỆNH"),
    ("tomtatketquacls",                 "KẾT QUẢ CLS"),
    ("quatrinhbenhlyvadienbienlamsang", "DIỄN BIẾN LÂM SÀNG"),
    # Treatment
    ("phuongphapdieutri",               "PHƯƠNG PHÁP ĐIỀU TRỊ"),
    ("pttt",                            "PHẪU THUẬT THỦ THUẬT"),
    ("tinhtrangnguoiravien",            "TÌNH TRẠNG RA VIỆN"),
    ("huongdieutritieptheo",            "HƯỚNG ĐIỀU TRỊ TIẾP THEO"),
    ("huongdieutri_out",                "HƯỚNG ĐIỀU TRỊ RA VIỆN"),
    # Lists (truncated)
    ("ds_xet_nghiem",                   "XÉT NGHIỆM"),
    ("ds_cdha",                         "CHẨN ĐOÁN HÌNH ẢNH"),
    ("ds_thuoc",                        "THUỐC"),
    ("ds_dich_vu",                      "DỊCH VỤ"),
]

# Numeric vitals assembled into one text section in build_document()
_VITALS_FIELDS: list[tuple[str, str, str]] = [
    ("chieucao",    "Chiều cao",            "cm"),
    ("cannang",     "Cân nặng",             "kg"),
    ("nhiptim",     "Nhịp tim",             "lần/phút"),
    ("nhietdo",     "Nhiệt độ",             "°C"),
    ("huyetap_high","Huyết áp tâm thu",     "mmHg"),
    ("huyetap_low", "Huyết áp tâm trương",  "mmHg"),
    ("nhiptho",     "Nhịp thở",             "lần/phút"),
]

_META_FIELDS: list[str] = [
    "ma_bn_an", "ho_ten", "dm_gioitinhid", "birthdayyear", "dm_tinhcode",
    "medicalrecorddate_in", "medicalrecorddate_out", "so_ngay_dieu_tri",
    "departmentid", "roomid", "bedid",
    "chandoan_in", "chandoan_in_icd10",
    "chandoan_out_main", "chandoan_out_main_icd10",
    "isbn_ut",
]

_NULL_VALUES = {"null", "nan", "none", "", "0", "0.0"}

log = logging.getLogger(__name__)


def _is_empty(val: str) -> bool:
    return val.strip().lower() in _NULL_VALUES


_LIST_FIELDS = {"ds_xet_nghiem", "ds_cdha", "ds_thuoc", "ds_dich_vu"}
_LIST_LIMIT  = 2000


def build_document(row: dict) -> str:
    parts: list[str] = []

    # Vitals — assemble numeric fields into one readable section
    vital_parts: list[str] = []
    for field, label, unit in _VITALS_FIELDS:
        val = str(row.get(field, "")).strip()
        if _is_empty(val):
            continue
        display = val.rstrip("0").rstrip(".") if "." in val else val
        vital_parts.append(f"{label}: {display} {unit}")
    if vital_parts:
        parts.append(f"[SINH HIỆU & NHÂN TRẮC] {' | '.join(vital_parts)}")

    for field, label in _TEXT_FIELDS:
        val = str(row.get(field, "")).strip()
        if _is_empty(val):
            continue
        if field in _LIST_FIELDS:
            val = val[:_LIST_LIMIT]
        parts.append(f"[{label}] {val}")

    return "\n".join(parts)


def build_metadata(row: dict) -> dict[str, str]:
    meta: dict[str, str] = {}
    for field in _META_FIELDS:
        val = row.get(field, "")
        meta[field] = "" if (val is None or str(val).strip().lower() in _NULL_VALUES) else str(val)
    return meta


_GEMINI_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-embedding-2:embedContent"
)


def _embed(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    import os
    import requests as _req
    api_key = os.environ["GOOGLE_API_KEY"]
    result: list[list[float]] = []
    for t in texts:
        payload = {
            "model": "models/gemini-embedding-2",
            "content": {"parts": [{"text": t}]},
            "taskType": task_type,
            "outputDimensionality": 768,
        }
        resp = _req.post(f"{_GEMINI_EMBED_URL}?key={api_key}", json=payload, timeout=120)
        resp.raise_for_status()
        result.append(resp.json()["embedding"]["values"])
    return result


def ingest_csv(csv_path: Path = DEFAULT_CSV, force: bool = False) -> dict:
    df = pd.read_csv(csv_path, skiprows=[1], dtype=str)
    df.fillna("", inplace=True)

    from app.services.chroma import get_collection
    collection = get_collection()

    existing = collection.get(include=["metadatas"])
    existing_hashes: dict[str, str] = {
        m["ma_bn_an"]: m.get("_hash", "")
        for m in (existing["metadatas"] or [])
        if m.get("ma_bn_an")
    }

    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict] = []
    skipped = 0

    for _, row in df.iterrows():
        record_id = str(row.get("ma_bn_an", "")).strip()
        if not record_id or _is_empty(record_id):
            continue

        doc = build_document(row)
        if not doc.strip():
            skipped += 1
            continue

        doc_hash = hashlib.md5(doc.encode()).hexdigest()
        if not force and existing_hashes.get(record_id) == doc_hash:
            skipped += 1
            continue

        meta = build_metadata(row)
        meta["_hash"] = doc_hash
        ids.append(record_id)
        docs.append(doc)
        metas.append(meta)

    if not ids:
        log.info("Nothing new to ingest (%d unchanged).", skipped)
        return {"added": 0, "skipped": skipped}

    log.info("Embedding %d record(s) via Google…", len(ids))
    embeddings = _embed(docs)

    log.info("Upserting into ChromaDB…")
    collection.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)

    log.info("Done — added: %d  skipped: %d", len(ids), skipped)
    return {"added": len(ids), "skipped": skipped}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m app.services.ingest")
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("ingest")
    pi.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    pi.add_argument("--force", action="store_true")
    sub.add_parser("stats")
    return p


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args = _build_parser().parse_args()
    if args.cmd == "ingest":
        print(f"\nIngest complete: {ingest_csv(args.csv, force=args.force)}")
    elif args.cmd == "stats":
        from app.services.chroma import get_collection
        col = get_collection()
        print(f"Collection 'medical_records': {col.count()} document(s)")


if __name__ == "__main__":
    main()