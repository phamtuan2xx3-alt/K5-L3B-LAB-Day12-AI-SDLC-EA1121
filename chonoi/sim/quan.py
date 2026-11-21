"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        # TODO(nhóm): khách dựng sẵn từ scenario (customers[]) và suy ra giữ chỗ (reserved).
        self.customers = [dict(c, reserved=c.get("reserved", {})) for c in scenario.get("customers", [])]
        for e in self.customers:
            ids.reserve(e["id"])
            e.setdefault("state", "waiting")
            e.setdefault("patience_ticks", int(round(t["patience_s"] * TICK)))
            e.setdefault("eat_ticks_left", 0)
            if "dish" in e and not e["reserved"] and e["dish"] in self.menu:
                e["reserved"] = dict(self.menu[e["dish"]]["recipe"])
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers if "table_id" in c}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Bếp đang nấu giảm cook_ticks_left, chuyển sang ready khi chín
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s.get("cook_ticks_left", 0) - 1)
                if s["cook_ticks_left"] == 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = 0
                    events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))
            elif s["state"] == "ready":
                s["ready_ticks"] = s.get("ready_ticks", 0) + 1

        # 2. Khách đang ăn hoặc đang đợi
        finished_eating = []
        for c in sort_by_id(self.customers):
            if c.get("state") == "eating":
                c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", 0) - 1)
                if c["eat_ticks_left"] == 0:
                    finished_eating.append(c)
            elif c.get("state") == "waiting":
                if c.get("patience_ticks", 0) > 0:
                    c["patience_ticks"] -= 1

        # Xử lý khách ăn xong -> thanh toán
        for c in finished_eating:
            dish = c.get("dish")
            price = self.menu[dish]["price"] if dish in self.menu else 0
            patience = c.get("patience_ticks", 0)
            max_patience = self.t["patience_s"] * TICK
            patience_ratio = patience / max_patience if max_patience > 0 else 0.0
            tip = 0
            if patience_ratio >= self.t["tip_min_patience_ratio"]:
                tip = int(round(price * self.t["tip_rate"]))
                self.reputation = min(float(self.t["reputation_max"]), round(self.reputation + self.t["tip_reputation"], 3))

            total_earned = price + tip
            self.money += total_earned
            self.earned += total_earned
            self.shift_earned += total_earned
            events.append(("paid", {"customer_id": c["id"], "money": price, "tip": tip}))
            if c in self.customers:
                self.customers.remove(c)

        # 3. Di chuyển người chơi
        self._move(inp)

        # 4. Tương tác (tối đa 1 interact mỗi tick)
        if inp.pressed("interact"):
            radius = self.t["interact_radius"]
            candidates = []
            for s in self.stoves:
                d = math.dist(self.pos, s["pos"])
                if d <= radius:
                    candidates.append((d, 0, s["id"], "stove", s))
            for tb in self.tables:
                d = math.dist(self.pos, tb["pos"])
                if d <= radius:
                    candidates.append((d, 1, tb["id"], "table", tb))

            if candidates:
                candidates.sort(key=lambda item: (item[0], item[1], item[2]))
                _, _, _, kind, target = candidates[0]

                if kind == "stove":
                    s = target
                    if s["state"] == "idle":
                        # Tìm khách đang chờ món mà chưa có bếp nào nấu
                        busy_cust_ids = {st.get("customer_id") for st in self.stoves if st["state"] in ("cooking", "ready") and st.get("customer_id")}
                        target_cust = None
                        for c in sort_by_id(self.customers):
                            if c.get("state") == "waiting" and c["id"] not in busy_cust_ids and c.get("dish") in self.menu:
                                target_cust = c
                                break

                        if target_cust is not None:
                            dish = target_cust["dish"]
                            recipe = self.menu[dish]["recipe"]
                            # Kiểm tra kho
                            can_cook = all(self.stock.get(ing, 0) >= qty for ing, qty in recipe.items())
                            if can_cook:
                                for ing, qty in recipe.items():
                                    self.stock[ing] = self.stock.get(ing, 0) - qty
                                if "reserved" in target_cust:
                                    target_cust["reserved"].clear()
                                s["customer_id"] = target_cust["id"]
                                s["state"] = "cooking"
                                s["dish"] = dish
                                s["cook_ticks_left"] = int(round(self.menu[dish]["cook_s"] * TICK))
                                s["ready_ticks"] = 0
                                events.append(("cook_started", {"stove_id": s["id"], "dish": dish}))

                    elif s["state"] == "ready":
                        if self.hand is None:
                            self.hand = s["dish"]
                            dish_picked = s["dish"]
                            s["state"] = "idle"
                            s["dish"] = None
                            s["customer_id"] = None
                            s["cook_ticks_left"] = 0
                            s["ready_ticks"] = 0
                            events.append(("dish_picked", {"stove_id": s["id"], "dish": dish_picked}))

                elif kind == "table":
                    tb = target
                    c = next((cust for cust in self.customers if cust.get("table_id") == tb["id"]), None)
                    if c is not None and c.get("state") == "waiting" and self.hand is not None:
                        if self.hand == c.get("dish"):
                            served_dish = self.hand
                            self.hand = None
                            c["state"] = "eating"
                            c["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                            events.append(("served", {"customer_id": c["id"], "table_id": tb["id"], "dish": served_dish}))

        # 5. Hết giờ đóng ca
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events
        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
