"""Soak headless (TICKET-04 mục 2): chạy N Ngày trong MỘT tiến trình bằng bot tất định.

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Mỗi Ngày đi qua gather -> quan -> shop; kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, earned, uy tín, cấp nâng cấp,
số Ngày và id tiếp tục xuyên suốt (cùng một DaySim). Bot chỉ đọc trạng thái sim (không RNG, không đồng hồ),
nên cùng seed -> cùng `results`. Chỉ `duration_s` là số đo thời gian thực.

soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}], duration_s}.
Mã thoát: 0 khi chạy xong (kể cả có crash, đã ghi vào crashes), 2 khi cờ sai, 1 khi không ghi được file.
"""

import argparse
import json
import math
import sys
import time
import traceback

from .contract import load_contract
from .ids import IdAllocator, id_key
from .inputs import BUTTONS_V11, LiveInputs
from .rng import Streams
from .sim.day import DaySim

MAX_TICKS_PER_DAY = 22_200  # TICKET-02: một Ngày không pause dài tối đa 22.200 tick
FLOWER_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _toward(src, dst):
    dx, dz = dst[0] - src[0], dst[1] - src[1]
    n = math.hypot(dx, dz)
    return [0.0, 0.0] if n < 1e-9 else [dx / n, dz / n]


class Bot:
    """Bot tất định: hái hoa trong kế hoạch rồi cập bến; ở quán nấu -> lấy -> phục vụ; Shop đóng ngay."""

    REACH = 0.8  # đứng trong 0.8 m mới bấm, nhỏ hơn mọi bán kính tương tác nên đối tượng gần nhất là đích

    def __init__(self):
        self.li = LiveInputs(buttons=BUTTONS_V11)
        self._pressed = False
        self._day = None
        self._harvested = set()

    def _press(self, move, button):
        # Nút chỉ tác động ở cạnh lên: bấm một tick rồi nhả một tick.
        if self._pressed:
            self.li.set(move=move, **{button: False})
            self._pressed = False
        else:
            self.li.set(move=move, **{button: True})
            self._pressed = True

    def _go(self, move):
        self.li.set(move=move, interact=False)
        self._pressed = False

    def act(self, day):
        sim = day.sub_sim
        if day.phase == "gather":
            self._gather(day, sim)
        elif day.phase == "quan":
            self._quan(sim)
        else:  # shop: đóng ngay, không mua (giữ bot đơn giản, tất định)
            self._press([0.0, 0.0], "shop_done")
        return self.li.advance()

    # ------------------------------------------------------------ buổi sáng
    def _gather(self, day, sim):
        if self._day != day.current_day:
            self._day, self._harvested = day.current_day, set()
        need = {k for k in day.current_plan.get("ingredients", {}) if k in FLOWER_KINDS}
        pos = sim.pos
        targets = [n for n in sorted(sim.nodes, key=lambda n: (n["pos"][0], id_key(n["id"])))
                   if n["kind"] in need and n["id"] not in self._harvested]
        if targets and len(sim.hold) < sim.t["hold_capacity"]:
            node = targets[0]
            goal = [node["pos"][0], 0.0]
            if _dist(pos, goal) <= self.REACH and pos[1] <= sim.t["surface_depth"]:
                if self._pressed:  # vừa bấm ở tick trước: coi như đã hái nút này
                    self._harvested.add(node["id"])
                self._press([0.0, 0.0], "interact")
            else:
                self._go(_toward(pos, goal))
            return
        dock = sim.t["dock_pos"]
        if _dist(pos, dock) <= self.REACH:
            self._press([0.0, 0.0], "interact")
        else:
            self._go(_toward(pos, dock))

    # ------------------------------------------------------------ buổi tối
    def _quan(self, sim):
        target = None
        if isinstance(sim.hand, dict):
            c = next((c for c in sim.customers if c["id"] == sim.hand["order_id"]), None)
            if c is not None:
                target = next(tb for tb in sim.tables if tb["id"] == c["table_id"])
        if target is None:
            target = next((s for s in sim.stoves if s["state"] == "ready"), None) if sim.hand is None else None
        if target is None and any(c["order_status"] == "reserved" and c["reserved"] for c in sim.customers):
            target = next((s for s in sim.stoves if s["state"] == "idle"), None)
        if target is None:
            self._go([0.0, 0.0])
        elif _dist(sim.pos, target["pos"]) <= self.REACH:
            self._press([0.0, 0.0], "interact")
        else:
            self._go(_toward(sim.pos, target["pos"]))


def run_soak(seed, days, tuning=None):
    tuning = tuning or load_contract()["tuning"]
    t0 = time.perf_counter()
    report = {"days": days, "days_completed": 0, "crashes": 0, "results": [], "duration_s": 0.0}
    mult = tuning.get("score", {}).get("reputation_multiplier", 100)
    try:
        day = DaySim(tuning, {}, Streams(seed), IdAllocator(), total_days=days)
        bot = Bot()
        for _ in range(days * MAX_TICKS_PER_DAY + 10):
            if day.done:
                break
            closing_day = day.current_day
            for name, _data in day.step(bot.act(day)):
                if name == "shop_end":
                    report["results"].append({
                        "day": closing_day, "earned": day.earned, "reputation": day.reputation,
                        "score": day.earned + mult * math.floor(day.reputation)})
        report["days_completed"] = day.days_completed
    except Exception:  # crash được đếm, không làm sập tiến trình soak
        report["crashes"] += 1
        traceback.print_exc(file=sys.stderr)
        report["days_completed"] = len(report["results"])
    report["duration_s"] = round(time.perf_counter() - t0, 3)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--days", type=int, required=True)
    p.add_argument("--out", required=True)
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if a.days < 1:
        print("--days phải >= 1", file=sys.stderr)
        return 2
    report = run_soak(a.seed, a.days)
    try:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except OSError as e:
        print(f"không ghi được {a.out}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
