"""Buổi tối — Mở Quán (`quan`).

Phục vụ thực khách chợ nổi:
- Khách đến theo lịch (120, 1020, 1920...) tại bàn có id nhỏ nhất.
- Chọn món có đủ nguyên liệu khả dụng từ kho (đã trừ phần đang giữ chỗ).
- Giữ chỗ nguyên liệu kho (reserved) khi gọi món.
- Nấu ăn tại bếp (cook_started, dish_ready), bưng bê (dish_picked) và phục vụ (served).
- Kiên nhẫn 60s (3600 ticks), ăn 10s (600 ticks).
- Trả tiền món + Tiền boa (20% giá món nếu kiên nhẫn còn >= 50%).
- Uy tín: +0.2 khi nhận boa dương, -0.5 khi khách bỏ về hết kiên nhẫn.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0

DEFAULT_MENU = {
    "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
    "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
    "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
    "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
    "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
    "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12, "price": 200},
}


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None):
        t = tuning.get("quan", {})
        self.t = t
        self.menu = dict(tuning.get("menu", DEFAULT_MENU))
        self.rng = streams
        self.ids = ids
        self.allowed_dishes = allowed_dishes  # Dùng khi lọc món theo day_plan

        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t.get("start_pos", [8, 5])))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        # Kho nguyên liệu: dict item -> count
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t.get("duration_s", 180) * 60)))
        self.reputation = float(scenario.get("reputation", t.get("reputation_initial", 3.0)))

        default_stoves = t.get("stoves", [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}])
        default_tables = t.get("tables", [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [13, 2]},
                                          {"id": "T3", "pos": [9, 6]}, {"id": "T4", "pos": [13, 6]}])

        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=int(s.get("cook_ticks_left", 0)),
                            ready_ticks=int(s.get("ready_ticks", 0)),
                            order_id=s.get("order_id"))
                       for s in self._merge(default_stoves, scenario.get("stoves", []))]
        self.tables = self._merge(default_tables, scenario.get("tables", []))

        # Khách hàng
        self.customers = []
        for c in scenario.get("customers", []):
            cust = dict(c)
            cust.setdefault("state", "waiting")
            cust.setdefault("patience_ticks", int(t.get("patience_s", 60) * 60))
            cust.setdefault("eat_ticks_left", 0)
            cust.setdefault("tip", 0)
            cust.setdefault("order_tick", 0)
            self.customers.append(cust)
            ids.reserve(cust["id"])

        for s in self.stoves:
            ids.reserve(s["id"])
        for tb in self.tables:
            ids.reserve(tb["id"])

        self.money = int(scenario.get("money", 0))
        self.earned = int(scenario.get("earned", 0))
        self.shift_earned = 0
        self.done = False
        self.reason = None
        self.tick_count = 0

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _reserved_stock(self) -> dict:
        """Tổng lượng nguyên liệu đang bị giữ bởi khách đang chờ."""
        reserved = {}
        for c in self.customers:
            if c.get("state") == "waiting" and c.get("dish") in self.menu:
                recipe = self.menu[c["dish"]]["recipe"]
                for ing, cnt in recipe.items():
                    reserved[ing] = reserved.get(ing, 0) + cnt
        return reserved

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.tick_count += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Bếp nấu: đếm lùi thời gian chín
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] <= 0:
                    s["state"] = "ready"
                    events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))

        # 2. Khách ăn xong & Khách hết kiên nhẫn
        remained_customers = []
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] -= 1
                if c["eat_ticks_left"] <= 0:
                    # Trả tiền món + boa
                    dish_info = self.menu.get(c["dish"], {"price": 50})
                    price = dish_info["price"]
                    tip = c.get("tip", 0)
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    if tip > 0:
                        self.reputation = min(5.0, round(self.reputation + 0.2, 2))
                    events.append(("paid", {
                        "customer_id": c["id"],
                        "table_id": c["table_id"],
                        "price": price,
                        "tip": tip,
                        "total": total
                    }))
                    continue  # Khách rời đi
            elif c["state"] == "waiting":
                c["patience_ticks"] -= 1
                if c["patience_ticks"] <= 0:
                    # Khách bỏ về vì hết kiên nhẫn
                    self.reputation = max(0.0, round(self.reputation - 0.5, 2))
                    events.append(("customer_left", {
                        "customer_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience"
                    }))
                    continue  # Khách rời đi, giải phóng nguyên liệu

            remained_customers.append(c)
        self.customers = remained_customers

        # 3. Khách mới đến theo lịch
        self._check_customer_arrival(events)

        # 4. Người chơi di chuyển
        self._move(inp)

        # 5. Tương tác (phím interact)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 6. Hết giờ ca quán
        if self.time_left_ticks <= 0:
            self._close_shift(events)

        return events

    def _check_customer_arrival(self, events):
        first_tick = int(self.t.get("first_customer_tick", 120))
        interval = int(round(self.t.get("customer_interval_s", 15) * 60))

        # Kiểm tra xem có đúng nhịp xuất hiện không
        is_arrival_tick = (self.tick_count == first_tick) or \
                          (self.tick_count > first_tick and (self.tick_count - first_tick) % interval == 0)

        if not is_arrival_tick:
            return

        # Tìm bàn trống có id nhỏ nhất
        occupied_tables = {c["table_id"] for c in self.customers}
        free_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied_tables]
        if not free_tables:
            return

        target_table = free_tables[0]

        # Lọc danh sách món có đủ nguyên liệu
        reserved = self._reserved_stock()
        candidate_dishes = []
        dish_pool = self.allowed_dishes if self.allowed_dishes else list(self.menu.keys())

        for dish_id in sorted(dish_pool):
            if dish_id not in self.menu:
                continue
            recipe = self.menu[dish_id]["recipe"]
            can_cook = all(self.stock.get(ing, 0) - reserved.get(ing, 0) >= cnt for ing, cnt in recipe.items())
            if can_cook:
                candidate_dishes.append(dish_id)

        if not candidate_dishes:
            # Không món nào đủ nguyên liệu
            events.append(("no_dish", {"table_id": target_table["id"]}))
            return

        # Chọn món ngẫu nhiên theo seed
        rng = self.rng.get("customer_dish")
        chosen_dish = candidate_dishes[rng.randint(0, len(candidate_dishes) - 1)]

        cust_id = self.ids.new("C")
        new_cust = {
            "id": cust_id,
            "table_id": target_table["id"],
            "dish": chosen_dish,
            "state": "waiting",
            "patience_ticks": int(self.t.get("patience_s", 60) * 60),
            "eat_ticks_left": 0,
            "tip": 0,
            "order_tick": self.tick_count
        }
        self.customers.append(new_cust)
        events.append(("customer_arrived", {
            "id": cust_id,
            "table_id": target_table["id"],
            "dish": chosen_dish
        }))

    def _handle_interact(self, events):
        """Tối đa 1 tương tác, ưu tiên đối tượng gần nhất (bếp trước bàn, rồi id)."""
        radius = float(self.t.get("interact_radius", 1.5))
        cands = []

        # Bếp
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= radius:
                cands.append((round(d, 6), 0, id_key(s["id"]), "stove", s))

        # Bàn
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius:
                cands.append((round(d, 6), 1, id_key(tb["id"]), "table", tb))

        if not cands:
            return

        cands.sort(key=lambda x: (x[0], x[1], x[2]))
        _, _, _, kind, target = cands[0]

        if kind == "stove":
            self._interact_stove(target, events)
        elif kind == "table":
            self._interact_table(target, events)

    def _interact_stove(self, s, events):
        if s["state"] == "idle":
            # Bếp rảnh: tìm đơn chờ nấu cũ nhất (order_tick nhỏ nhất, rồi table_id)
            waiting_custs = [c for c in self.customers if c["state"] == "waiting" and not any(st.get("order_id") == c["id"] for st in self.stoves)]
            if not waiting_custs:
                return
            waiting_custs.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
            cust = waiting_custs[0]

            # Bếp bắt đầu nấu: trừ nguyên liệu kho
            dish_id = cust["dish"]
            recipe = self.menu[dish_id]["recipe"]
            for ing, cnt in recipe.items():
                self.stock[ing] = self.stock.get(ing, 0) - cnt

            cook_s = self.menu[dish_id]["cook_s"]
            s["state"] = "cooking"
            s["dish"] = dish_id
            s["order_id"] = cust["id"]
            s["cook_ticks_left"] = int(round(cook_s * 60))
            events.append(("cook_started", {
                "stove_id": s["id"],
                "dish": dish_id,
                "order_id": cust["id"]
            }))
        elif s["state"] == "ready":
            # Bếp chín: player lấy món nếu tay rỗng
            if self.hand is None:
                self.hand = s["dish"]
                order_id = s.get("order_id")
                events.append(("dish_picked", {
                    "stove_id": s["id"],
                    "dish": self.hand,
                    "order_id": order_id
                }))
                s["state"] = "idle"
                s["dish"] = None
                s["order_id"] = None

    def _interact_table(self, tb, events):
        if self.hand is None:
            return
        # Tìm khách tại bàn đang chờ đúng món trên tay
        matched = [c for c in self.customers if c["table_id"] == tb["id"] and c["state"] == "waiting" and c["dish"] == self.hand]
        if not matched:
            return

        cust = matched[0]
        dish_id = self.hand
        self.hand = None
        cust["state"] = "eating"
        cust["eat_ticks_left"] = int(round(self.t.get("eat_s", 10) * 60))

        # Tính tiền boa: nếu còn >= 50% kiên nhẫn
        total_patience = int(self.t.get("patience_s", 60) * 60)
        price = self.menu[dish_id]["price"]
        if cust["patience_ticks"] >= total_patience * 0.5:
            tip = math.floor(price * self.t.get("tip_rate", 0.2))
        else:
            tip = 0
        cust["tip"] = tip

        events.append(("served", {
            "table_id": tb["id"],
            "customer_id": cust["id"],
            "dish": dish_id,
            "tip": tip
        }))

    def _close_shift(self, events):
        self.done = True
        self.reason = "time"
        # Khách còn đang ăn thanh toán ngay
        for c in self.customers:
            if c["state"] == "eating":
                dish_info = self.menu.get(c["dish"], {"price": 50})
                price = dish_info["price"]
                tip = c.get("tip", 0)
                total = price + tip
                self.money += total
                self.earned += total
                self.shift_earned += total

        events.append(("quan_end", {
            "reason": "time",
            "money": self.money,
            "earned": self.earned,
            "shift_earned": self.shift_earned,
            "reputation": self.reputation
        }))

    def _move(self, inp):
        speed = self.t.get("walk_speed", 4.0)
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t.get("bounds", {"x": [0, 16], "z": [0, 10]})
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
