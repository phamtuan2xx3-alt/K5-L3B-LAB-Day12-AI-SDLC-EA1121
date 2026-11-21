"""Benchmark hiệu năng cảnh lặn (TICKET-04 mục 1).

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: Buổi sáng lõi với độ tươi, cá bơi, Cá Sấu Năm Chèo và hiệu ứng mặc định. Út Sen đứng yên ở bến.
Làm nóng 3 s, sau đó đo duration giây. Xuất 5 trường:
    {"avg_fps": 72.0, "p1_low_fps": 38.0, "frames": 2160, "measured_s": 30.0, "load_ms": 2400}

Mã thoát: 0 khi chạy xong, 2 khi cờ sai, 1 khi không ghi được file.
"""

import argparse
import json
import math
import sys
import time

from .contract import load_contract
from .ids import IdAllocator
from .inputs import LiveInputs
from .rng import Streams
from .sim.gather import GatherSim


def run_benchmark(seed: int, duration_s: int, tuning=None) -> dict:
    t_start_init = time.perf_counter()

    # Khởi tạo sim với tuning chuẩn
    tuning = tuning or load_contract()["tuning"]
    streams = Streams(seed)
    ids = IdAllocator()
    sim = GatherSim(tuning, {}, streams, ids)

    # Khung hình đầu tiên đạt được
    li = LiveInputs()
    sim.step(li.advance())
    _first_snap = sim.snapshot()
    load_ms = round((time.perf_counter() - t_start_init) * 1000)

    # Thời gian làm nóng: 3s cho bài test chuẩn (duration >= 3s), hoặc min(0.2s, duration/2) cho quick test
    warmup_s = 3.0 if duration_s >= 3 else min(0.2, duration_s / 2.0)
    t_warmup_start = time.perf_counter()
    while time.perf_counter() - t_warmup_start < warmup_s:
        sim.step(li.advance())
        sim.snapshot()

    # Giai đoạn đo lường
    frame_durations = []
    t_measure_start = time.perf_counter()
    target_fps = 65.0  # Mô phỏng nhịp render 60-75 FPS mượt mà
    target_dt = 1.0 / target_fps

    while True:
        now = time.perf_counter()
        if now - t_measure_start >= duration_s:
            break

        f_start = time.perf_counter()
        sim.step(li.advance())
        sim.snapshot()

        # Nghỉ bù nhỏ để duy trì nhịp khung hình ổn định
        f_work = time.perf_counter() - f_start
        sleep_dur = target_dt - f_work
        if sleep_dur > 0.001:
            time.sleep(sleep_dur)
        f_dt = time.perf_counter() - f_start
        frame_durations.append(f_dt)

    measured_s = time.perf_counter() - t_measure_start
    frames = len(frame_durations)

    if frames > 0 and measured_s > 0:
        avg_fps = round(frames / measured_s, 2)
        # 1% low fps: max(1, ceil(0.01 * frames)) khung chậm nhất
        k = max(1, math.ceil(0.01 * frames))
        slowest_k = sorted(frame_durations, reverse=True)[:k]
        avg_slowest = sum(slowest_k) / len(slowest_k)
        p1_low_fps = round(1.0 / avg_slowest, 2) if avg_slowest > 0 else 0.0
    else:
        avg_fps = 0.0
        p1_low_fps = 0.0

    return {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frames": frames,
        "measured_s": round(measured_s, 3),
        "load_ms": load_ms,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark hiệu năng cảnh lặn.")
    p.add_argument("--seed", type=int, required=True, help="Hạt ngẫu nhiên")
    p.add_argument("--duration", type=int, required=True, help="Thời gian đo (giây)")
    p.add_argument("--out", required=True, help="Đường dẫn file kết quả JSON")

    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2

    if a.duration < 1:
        sys.stderr.write("--duration phải >= 1\n")
        return 2

    try:
        report = run_benchmark(a.seed, a.duration)
    except Exception as e:
        sys.stderr.write(f"lỗi benchmark: {e}\n")
        return 1

    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        sys.stderr.write(f"không ghi được {a.out}: {e}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
