"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Luật PRD-0 mục F, Quán:
  Lát 3 (DEV 3): vòng đời khách — sim/customers.py (lịch, bàn, giữ chỗ, kiên nhẫn, rời, trả tiền).
  Lát 3 (DEV 4): kho khả dụng và tiêu phần giữ — _get_available_stock, _consume_reservation.
  Lát 4 (DEV 5): bếp, bưng, phục vụ, boa — _tick_stoves, _finish_cooking, _interact.
"""

import math

from ..ids import sort_by_id
from . import customers as cust
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        # v1.1 --mode day: id món trong kế hoạch Ngày (list hoặc map id -> suất). None = cả menu.
        self.allowed_dishes = None if allowed_dishes is None else sorted(allowed_dishes)
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
        # Lát 3 (DEV 3): khách fixture + giữ chỗ suy ra + kiểm mâu thuẫn — xem sim/customers.py.
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.customers = cust.init_customers(self, scenario.get("customers", []), self.random_customers)
        for e in self.customers:
            ids.reserve(e["id"])
        # day (v1.1) bàn giao tiền/earned xuyên Ngày qua scenario nội bộ; quán độc lập bắt đầu từ 0.
        self.money = scenario.get("money", 0)
        self.earned = scenario.get("earned", 0)
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

    def _get_available_stock(self) -> dict:
        """Tính phần kho chưa được khách giữ chỗ."""
        available = dict(self.stock)
        for customer in self.customers:
            for ingredient, quantity in customer.get("reserved", {}).items():
                available[ingredient] = available.get(ingredient, 0) - quantity
        return available

    def _find_cookable_dish(self, available_stock) -> tuple[str, dict] | None:
        """Trả món đầu tiên đủ nguyên liệu và bản sao công thức để giữ chỗ."""
        for dish, details in self.menu.items():
            recipe = details["recipe"]
            if all(available_stock.get(ingredient, 0) >= quantity
                   for ingredient, quantity in recipe.items()):
                return dish, dict(recipe)
        return None

    def _choose_dish_for_customer(self, events) -> tuple[str, dict] | None:
        """Sau khi tìm được bàn, trả (món, reserved) để lưu vào khách mới."""
        order = self._find_cookable_dish(self._get_available_stock())
        if order is None:
            events.append(("no_dish", {}))
        return order

    def _consume_reservation(self, customer) -> bool:
        """Trừ kho khi bếp bắt đầu nấu. Trả False nếu chưa thể trừ đủ."""
        reserved = customer.get("reserved", {})
        if not reserved or any(self.stock.get(ingredient, 0) < quantity
                               for ingredient, quantity in reserved.items()):
            return False
        for ingredient, quantity in reserved.items():
            self.stock[ingredient] = self.stock.get(ingredient, 0) - quantity
        customer["reserved"] = {}
        return True

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        # 1. đồng hồ, timer ca; kiên nhẫn + timer ăn (lát 3)
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        cust.tick_timers(self)
        self._tick_stoves()
        # 2. xét bếp theo id: nấu xong -> ready, ready_ticks = 0 (lát 4)
        self._finish_cooking(events)
        # 3. di chuyển rồi tối đa MỘT interact (lát 4)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        # 4. theo id bàn: ăn xong trả tiền, hết kiên nhẫn rời, đóng ca dọn khách (lát 3)
        closing = self.time_left_ticks <= 0
        cust.settle_tables(self, events, closing)
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        else:
            # 5. lượt khách mới theo lịch, no_dish (lát 3)
            cust.maybe_spawn(self, events)
        return events

    # ------------------------------------------------------------ lát 4: bếp, bưng, phục vụ
    # Ý tưởng và test gốc của DEV 5 (moyymochi11); chỉnh theo PRD-0 F/E khi tích hợp với lát 3:
    # payload món {order_id,dish_id,base_price}, bếp lấy đơn reserved cũ nhất, boa chốt lúc phục vụ.

    def _tick_stoves(self):
        """Bước 1: giảm timer nấu; chỉ tăng ready_ticks cho món đã ready từ đầu bước."""
        for s in self.stoves:
            if s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            elif s["state"] == "ready":
                s["ready_ticks"] += 1

    def _finish_cooking(self, events):
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"], s["ready_ticks"] = "ready", 0
                events.append(("dish_ready", {"stove_id": s["id"], "order_id": s["dish"]["order_id"],
                                              "dish_id": s["dish"]["dish_id"]}))

    def _interact(self, events):
        """Chọn MỘT đối tượng trong bán kính theo (khoảng cách, bếp trước bàn, id); không làm được thì bỏ lượt."""
        from ..ids import id_key
        radius = self.t["interact_radius"]
        cands = [(math.dist(self.pos, o["pos"]), rank, id_key(o["id"]), kind, o)
                 for rank, kind, objs in ((0, "stove", self.stoves), (1, "table", self.tables))
                 for o in objs if math.dist(self.pos, o["pos"]) <= radius]
        if not cands:
            return
        _, _, _, kind, target = min(cands, key=lambda c: c[:3])
        if kind == "stove":
            if target["state"] == "idle":
                self._start_cooking(target, events)
            elif target["state"] == "ready" and self.hand is None:
                self._pick_dish(target, events)
        else:
            self._serve(target, events)

    def _start_cooking(self, stove, events):
        """Bếp idle lấy đơn reserved cũ nhất (order_tick rồi id bàn), tiêu đúng phần giữ, chốt giá."""
        from ..ids import id_key
        orders = [c for c in self.customers if c["order_status"] == "reserved" and c["reserved"]]
        if not orders:
            return
        c = min(orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        items = sorted(k for k, n in c["reserved"].items() for _ in range(n))
        if not self._consume_reservation(c):  # helper kho của DEV 4
            return
        dish = self.menu[c["dish_id"]]
        c["order_status"], c["base_price"] = "assigned", dish["price"]
        stove.update(state="cooking", dish={"order_id": c["id"], "dish_id": c["dish_id"], "base_price": dish["price"]},
                     cook_ticks_left=int(round(dish["cook_s"] * TICK)), ready_ticks=0)
        events.append(("cook_started", {"stove_id": stove["id"], "order_id": c["id"], "dish_id": c["dish_id"],
                                        "items": items, "base_price": dish["price"]}))

    def _pick_dish(self, stove, events):
        self.hand = stove["dish"]
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
        events.append(("dish_picked", {"stove_id": stove["id"], "order_id": self.hand["order_id"],
                                       "dish_id": self.hand["dish_id"]}))

    def _serve(self, table, events):
        """Bàn nhận đúng order_id: khách ăn với timer đầy; boa chốt theo kiên nhẫn còn lại sau bước 1."""
        c = next((x for x in self.customers if x["table_id"] == table["id"]), None)
        if c is None or c["state"] != "waiting" or not isinstance(self.hand, dict) \
                or self.hand["order_id"] != c["id"]:
            return
        base = self.hand["base_price"]
        full = cust.to_ticks(self.t["patience_s"])
        tip = math.floor(base * self.t["tip_rate"]) \
            if c["patience_ticks_left"] / full >= self.t["tip_min_patience_ratio"] else 0
        self.hand = None
        c.update(state="eating", order_status="served", eat_ticks_left=cust.to_ticks(self.t["eat_s"]),
                 base_price=base, tip=tip)
        events.append(("served", {"order_id": c["id"], "table_id": table["id"], "dish_id": c["dish_id"],
                                  "patience_ticks_left": c["patience_ticks_left"], "base_price": base, "tip": tip}))

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
