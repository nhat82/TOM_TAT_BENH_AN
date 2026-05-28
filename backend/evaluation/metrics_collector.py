"""
Background system-resource collector for evaluation runs.

Collects per-stage and per-query:
  CPU %, RAM (MB), GPU compute + VRAM (pynvml, optional),
  Disk I/O (MB), Network I/O (MB), query latency, token counts.

Usage:
    col = MetricsCollector()
    col.start()

    with col.stage("collect"):
        ...

    with col.stage("judge"):
        ...

    col.stop()
    summary = col.summary()   # dict ready for JSON / markdown
"""
from __future__ import annotations

import statistics
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator, Optional

try:
    import psutil as _psutil
    _PSUTIL_OK = True
except ImportError:
    _psutil = None  # type: ignore[assignment]
    _PSUTIL_OK = False

# Optional GPU support (nvidia only)
try:
    import pynvml as _pynvml  # type: ignore[import]
    _pynvml.nvmlInit()
    _GPU_HANDLE        = _pynvml.nvmlDeviceGetHandleByIndex(0)
    _GPU_NAME: str     = _pynvml.nvmlDeviceGetName(_GPU_HANDLE)
    _GPU_VRAM_TOTAL_MB = _pynvml.nvmlDeviceGetMemoryInfo(_GPU_HANDLE).total / 1e6
    _NVML_OK           = True
except Exception:
    _pynvml = None  # type: ignore[assignment]
    _GPU_HANDLE = _GPU_NAME = _GPU_VRAM_TOTAL_MB = None
    _NVML_OK = False

# ── token cost table (USD per 1 M tokens) ─────────────────────────────────────
_COST_PER_1M: dict[str, dict[str, float]] = {
    "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash":      {"input": 0.10,  "output": 0.40},
    "gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash":      {"input": 0.15,  "output": 0.60},
    "gemini-3.1-flash-lite": {"input": 0.075, "output": 0.30},
}
_DEFAULT_COST = {"input": 0.10, "output": 0.40}


def estimate_cost_usd(model: str, input_tok: int, output_tok: int) -> float:
    rates = _COST_PER_1M.get(model, _DEFAULT_COST)
    return round(input_tok * rates["input"] / 1e6 + output_tok * rates["output"] / 1e6, 6)


# ── per-query record ──────────────────────────────────────────────────────────

@dataclass
class QueryMetrics:
    patient_id: str
    question_preview: str
    total_latency_s: float = 0.0
    inference_latency_s: float = 0.0   # ainvoke only, excluding rate-limit sleeps
    ttft_s: Optional[float] = None     # None = non-streaming
    input_tokens_est: int = 0
    output_tokens_est: int = 0
    judge_input_tokens: int = 0
    judge_output_tokens: int = 0
    error: Optional[str] = None

    @property
    def tokens_per_second(self) -> Optional[float]:
        if self.inference_latency_s > 0 and self.output_tokens_est > 0:
            return round(self.output_tokens_est / self.inference_latency_s, 2)
        return None

    @property
    def total_tokens(self) -> int:
        return (self.input_tokens_est + self.output_tokens_est +
                self.judge_input_tokens + self.judge_output_tokens)


# ── per-stage record ──────────────────────────────────────────────────────────

@dataclass
class _StageData:
    name: str
    t_start: float = 0.0
    t_end: float = 0.0
    cpu_pct: list[float] = field(default_factory=list)
    ram_mb: list[float] = field(default_factory=list)
    gpu_util_pct: list[float] = field(default_factory=list)
    gpu_mem_mb: list[float] = field(default_factory=list)
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    net_recv_mb: float = 0.0
    net_sent_mb: float = 0.0

    @property
    def duration_s(self) -> float:
        return round(self.t_end - self.t_start, 3)

    def _stat(self, data: list[float]) -> tuple[Optional[float], Optional[float]]:
        if not data:
            return None, None
        return round(statistics.mean(data), 1), round(max(data), 1)

    def to_dict(self) -> dict:
        cpu_avg, cpu_peak = self._stat(self.cpu_pct)
        ram_avg, ram_peak = self._stat(self.ram_mb)
        gpu_avg, gpu_peak = self._stat(self.gpu_util_pct)
        _, gmem_peak      = self._stat(self.gpu_mem_mb)
        return {
            "duration_s":        self.duration_s,
            "cpu_avg_pct":       cpu_avg,
            "cpu_peak_pct":      cpu_peak,
            "ram_avg_mb":        ram_avg,
            "ram_peak_mb":       ram_peak,
            "gpu_util_avg_pct":  gpu_avg,
            "gpu_util_peak_pct": gpu_peak,
            "gpu_vram_peak_mb":  gmem_peak,
            "disk_read_mb":      round(self.disk_read_mb,  3),
            "disk_write_mb":     round(self.disk_write_mb, 3),
            "net_recv_mb":       round(self.net_recv_mb,   3),
            "net_sent_mb":       round(self.net_sent_mb,   3),
        }


# ── collector ─────────────────────────────────────────────────────────────────

class MetricsCollector:
    _SAMPLE_HZ = 0.5  # seconds between background samples

    def __init__(self) -> None:
        self._lock    = threading.Lock()
        self._stages: dict[str, _StageData] = {}
        self._active: Optional[_StageData]  = None
        self._queries: list[QueryMetrics]   = []
        self._cold_start_s: Optional[float] = None
        self._running  = False
        self._thread: Optional[threading.Thread] = None

        if _PSUTIL_OK:
            self._proc = _psutil.Process()
            self._proc.cpu_percent()  # warm-up: first call always returns 0.0

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    # ── stage context manager ─────────────────────────────────────────────────

    @contextmanager
    def stage(self, name: str) -> Generator[None, None, None]:
        s   = _StageData(name=name, t_start=time.perf_counter())
        io0 = self._io_snapshot()
        with self._lock:
            self._stages[name] = s
            self._active       = s
        try:
            yield
        finally:
            io1   = self._io_snapshot()
            s.t_end = time.perf_counter()
            if io0 and io1:
                (disk0, net0), (disk1, net1) = io0, io1
                s.disk_read_mb  = (disk1.read_bytes  - disk0.read_bytes)  / 1e6
                s.disk_write_mb = (disk1.write_bytes - disk0.write_bytes) / 1e6
                s.net_recv_mb   = (net1.bytes_recv   - net0.bytes_recv)   / 1e6
                s.net_sent_mb   = (net1.bytes_sent   - net0.bytes_sent)   / 1e6
            with self._lock:
                if self._active is s:
                    self._active = None

    # ── per-query recording ───────────────────────────────────────────────────

    def record_query(self, qm: QueryMetrics) -> None:
        with self._lock:
            self._queries.append(qm)

    def set_cold_start(self, seconds: float) -> None:
        self._cold_start_s = round(seconds, 3)

    def update_judge_tokens(self, patient_id: str, question_preview: str,
                             judge_in: int, judge_out: int) -> None:
        key = (patient_id, question_preview[:65])
        with self._lock:
            for qm in self._queries:
                if (qm.patient_id, qm.question_preview[:65]) == key:
                    qm.judge_input_tokens  = judge_in
                    qm.judge_output_tokens = judge_out
                    return

    # ── background sampler ────────────────────────────────────────────────────

    def _sample_loop(self) -> None:
        while self._running:
            try:
                if _PSUTIL_OK:
                    cpu = self._proc.cpu_percent(interval=None)
                    ram = self._proc.memory_info().rss / 1e6
                else:
                    cpu = ram = 0.0

                gpu_util = gpu_mem = None
                if _NVML_OK and _GPU_HANDLE:
                    try:
                        util     = _pynvml.nvmlDeviceGetUtilizationRates(_GPU_HANDLE)
                        memi     = _pynvml.nvmlDeviceGetMemoryInfo(_GPU_HANDLE)
                        gpu_util = float(util.gpu)
                        gpu_mem  = memi.used / 1e6
                    except Exception:
                        pass

                with self._lock:
                    if self._active:
                        self._active.cpu_pct.append(cpu)
                        self._active.ram_mb.append(ram)
                        if gpu_util is not None:
                            self._active.gpu_util_pct.append(gpu_util)
                        if gpu_mem is not None:
                            self._active.gpu_mem_mb.append(gpu_mem)
            except Exception:
                pass
            time.sleep(self._SAMPLE_HZ)

    # ── I/O snapshot ──────────────────────────────────────────────────────────

    @staticmethod
    def _io_snapshot():
        if not _PSUTIL_OK:
            return None
        try:
            return _psutil.disk_io_counters(), _psutil.net_io_counters()
        except Exception:
            return None

    # ── summary ───────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        valid = [q for q in self._queries if not q.error]
        errs  = [q for q in self._queries if q.error]

        inf_lats   = [q.inference_latency_s for q in valid if q.inference_latency_s > 0]
        total_lats = [q.total_latency_s     for q in valid if q.total_latency_s > 0]

        p_in  = sum(q.input_tokens_est   for q in valid)
        p_out = sum(q.output_tokens_est  for q in valid)
        j_in  = sum(q.judge_input_tokens  for q in self._queries)
        j_out = sum(q.judge_output_tokens for q in self._queries)

        return {
            "gpu_available":     _NVML_OK,
            "gpu_name":          _GPU_NAME,
            "gpu_vram_total_mb": _GPU_VRAM_TOTAL_MB,
            "cold_start_s":      self._cold_start_s,
            "error_rate":        round(len(errs) / len(self._queries), 3) if self._queries else 0.0,
            "latency": {
                "inference_avg_s": _mean(inf_lats),
                "inference_p50_s": _pct(inf_lats, 50),
                "inference_p95_s": _pct(inf_lats, 95),
                "inference_min_s": round(min(inf_lats), 3) if inf_lats else None,
                "inference_max_s": round(max(inf_lats), 3) if inf_lats else None,
                "total_avg_s":     _mean(total_lats),
                "total_p50_s":     _pct(total_lats, 50),
                "total_p95_s":     _pct(total_lats, 95),
                "total_min_s":     round(min(total_lats), 3) if total_lats else None,
                "total_max_s":     round(max(total_lats), 3) if total_lats else None,
            },
            "throughput_rps": (
                round(len(valid) / sum(total_lats), 4) if total_lats else None
            ),
            "tokens": {
                "pipeline_input_est":  p_in,
                "pipeline_output_est": p_out,
                "judge_input":         j_in,
                "judge_output":        j_out,
                "total":               p_in + p_out + j_in + j_out,
            },
            "stages": {n: s.to_dict() for n, s in self._stages.items()},
            "per_query": [
                {
                    "patient_id":           q.patient_id,
                    "question_preview":     q.question_preview,
                    "inference_latency_s":  q.inference_latency_s,
                    "total_latency_s":      q.total_latency_s,
                    "ttft_s":               q.ttft_s,
                    "tokens_per_second":    q.tokens_per_second,
                    "input_tokens_est":     q.input_tokens_est,
                    "output_tokens_est":    q.output_tokens_est,
                    "judge_input_tokens":   q.judge_input_tokens,
                    "judge_output_tokens":  q.judge_output_tokens,
                    "total_tokens":         q.total_tokens,
                    "error":                q.error,
                }
                for q in self._queries
            ],
        }


# ── statistics helpers ────────────────────────────────────────────────────────

def _mean(data: list[float]) -> Optional[float]:
    return round(statistics.mean(data), 3) if data else None


def _pct(data: list[float], p: int) -> Optional[float]:
    if not data:
        return None
    s  = sorted(data)
    k  = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)
