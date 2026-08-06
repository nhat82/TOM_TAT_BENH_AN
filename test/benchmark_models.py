"""
Benchmark the live /api/chat endpoint.

Calls the running backend directly over HTTP (SSE) instead of importing
backend packages, so it never needs a direct DB/model connection itself —
only the server does.

Metrics per question:
  - time to first token (TTFT, seconds)
  - error (bool)
  - tool call count (reported by the server in the "done" event)

The backend binds one model at a time (see agent_package/agent_chat.py).
To compare two models: set the model in agent_chat.py, (re)start the
backend, run this script with --model-label naming that model, repeat for
the other model, then diff the two JSON reports.

Usage:
  python test/benchmark_models.py --model-label local/qwen3:14b
  python test/benchmark_models.py --base-url http://localhost:8000 --patient-ids BA2025000001
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import httpx
from httpx_sse import connect_sse

QUESTIONS_BY_PATIENT: dict[str, list[str]] = {
    # Viêm phổi mắc phải cộng đồng
    "BA2025000001": [
        "Chẩn đoán chính lúc ra viện của bệnh nhân là gì?",
        "Lý do bệnh nhân đến khám là gì?",
        "Kết quả xét nghiệm CRP và cấy đờm của bệnh nhân như thế nào?",
        "Bệnh nhân được điều trị bằng kháng sinh gì?",
        "Hướng điều trị tiếp theo sau khi ra viện là gì?",
    ],
    # Viêm ruột thừa cấp - phẫu thuật nội soi
    "BA2025000002": [
        "Bệnh nhân được chẩn đoán mắc bệnh gì?",
        "Bệnh nhân có tiền sử dị ứng thuốc không?",
        "Bệnh nhân đã được phẫu thuật gì, vào ngày nào?",
        "Kết quả siêu âm bụng của bệnh nhân cho thấy điều gì?",
        "Sau phẫu thuật bệnh nhân hồi phục ra sao?",
    ],
    # Đái tháo đường type 2 biến chứng thận
    "BA2025000003": [
        "Chẩn đoán chính của bệnh nhân là gì?",
        "Tiền sử bệnh của bệnh nhân gồm những gì?",
        "Chỉ số HbA1c và creatinin của bệnh nhân là bao nhiêu?",
        "Bệnh nhân được điều trị bằng loại insulin nào?",
        "Hướng điều trị tiếp theo và lịch tái khám của bệnh nhân là gì?",
    ],
    # Gãy đầu dưới xương quay - ngoại trú, bó bột
    "BA2025000004": [
        "Bệnh nhân nhập viện vì lý do gì?",
        "Kết quả chụp X-quang cổ tay của bệnh nhân cho thấy tổn thương gì?",
        "Bệnh nhân đã được xử trí thủ thuật gì?",
        "Tình trạng bệnh nhân lúc ra viện như thế nào?",
        "Bệnh nhân cần tái khám và tháo bột khi nào?",
    ],
    # Đột quỵ nhồi máu não - chuyển viện
    "BA2025000005": [
        "Chẩn đoán chính của bệnh nhân khi ra viện là gì?",
        "Bệnh nhân có tiền sử bệnh gì trước khi nhập viện?",
        "Kết quả chụp CT và MRI sọ não của bệnh nhân như thế nào?",
        "Sức cơ tay chân trái của bệnh nhân thay đổi ra sao trong quá trình điều trị?",
        "Bệnh nhân được chuyển đến đâu và vì lý do gì?",
    ],
    # Sốt xuất huyết Dengue - đang điều trị (chưa ra viện)
    "BA2025000006": [
        "Bệnh nhân nhập viện với triệu chứng gì?",
        "Kết quả xét nghiệm tiểu cầu và Hematocrit của bệnh nhân thay đổi ra sao qua các ngày?",
        "Xét nghiệm NS1 và IgM Dengue của bệnh nhân cho kết quả gì?",
        "Bệnh nhân đang được điều trị bằng phác đồ gì?",
        "Tình trạng ra viện của bệnh nhân hiện tại như thế nào?",
    ],
}


def _run_one(client: httpx.Client, patient_id: str, question: str) -> dict:
    payload = {"patient_id": patient_id, "query": question, "chat_history": []}
    t_start = time.perf_counter()
    ttft = None
    tool_calls = None
    error = None

    try:
        with connect_sse(client, "POST", "/api/chat", json=payload, timeout=120) as event_source:
            for sse in event_source.iter_sse():
                event = json.loads(sse.data)
                if event["type"] == "token" and ttft is None:
                    ttft = time.perf_counter() - t_start
                elif event["type"] == "done":
                    tool_calls = event.get("tool_calls")
                elif event["type"] == "error":
                    error = event.get("detail", "unknown error")
    except httpx.HTTPError as exc:
        error = str(exc)

    return {
        "question": question,
        "ttft_s": round(ttft, 3) if ttft is not None else None,
        "tool_calls": tool_calls,
        "error": error,
    }


def _run_all(client: httpx.Client, patient_ids: list[str]) -> dict:
    results = []
    for pid in patient_ids:
        questions = QUESTIONS_BY_PATIENT[pid]
        for i, q in enumerate(questions):
            print(f"  [{pid} {i+1}/{len(questions)}] {q[:60]}...")
            r = _run_one(client, pid, q)
            r["patient_id"] = pid
            status = "ERROR" if r["error"] else "ok"
            print(f"      ttft={r['ttft_s']}s tools={r['tool_calls']} [{status}]")
            results.append(r)

    ttfts = [r["ttft_s"] for r in results if r["ttft_s"] is not None]
    errors = [r for r in results if r["error"]]
    tool_counts = [r["tool_calls"] for r in results if not r["error"] and r["tool_calls"] is not None]

    return {
        "per_question": results,
        "summary": {
            "ttft_avg_s": round(statistics.mean(ttfts), 3) if ttfts else None,
            "ttft_p50_s": round(statistics.median(ttfts), 3) if ttfts else None,
            "error_rate": round(len(errors) / len(results), 3),
            "tool_calls_avg": round(statistics.mean(tool_counts), 2) if tool_counts else None,
        },
    }


def _print_summary(model_label: str, report: dict) -> None:
    s = report["summary"]
    print("\n" + "=" * 60)
    print(f"  SUMMARY — {model_label}")
    print("=" * 60)
    print(f"  TTFT avg:        {s['ttft_avg_s']} s")
    print(f"  TTFT p50:        {s['ttft_p50_s']} s")
    print(f"  Error rate:      {s['error_rate']}")
    print(f"  Tool calls avg:  {s['tool_calls_avg']}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the live /api/chat endpoint.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--model-label", required=True,
        help="Label for the model currently bound in agent_chat.py (used only for the report).",
    )
    parser.add_argument(
        "--patient-ids", nargs="+", default=list(QUESTIONS_BY_PATIENT),
        choices=list(QUESTIONS_BY_PATIENT),
    )
    args = parser.parse_args()

    print(f"\n=== {args.model_label} ({args.base_url}) ===")
    with httpx.Client(base_url=args.base_url) as client:
        report = _run_all(client, args.patient_ids)

    _print_summary(args.model_label, report)

    safe_label = args.model_label.replace("/", "_").replace(":", "_")
    out_path = Path(__file__).parent / f"benchmark_report_{safe_label}.json"
    out_path.write_text(
        json.dumps({"model": args.model_label, **report}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nJSON report -> {out_path}")


if __name__ == "__main__":
    main()
