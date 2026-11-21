"""Chế độ trọn vẹn một ngày ở chợ nổi (`day`).

Vòng lặp:
  DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> Ngày kế tiếp (tối đa 5 ngày).
"""

from ..ids import IdAllocator
from ..rng import Streams
from .gather import GatherSim
from .quan import QuanSim

PRESET_DAY_PLANS = [
    {
        "day": 1,
        "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
        "ingredients": {"ca_loc": 3, "bong_sung": 6}
    },
    {
        "day": 2,
        "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2},
        "ingredients": {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2}
    },
    {
        "day": 3,
        "dishes": {"goi_bong_sung": 2, "canh_chua_ca_loc": 2, "ca_keo_nuong": 2},
        "ingredients": {"bong_sung": 4, "ca_loc": 2, "bong_dien_dien": 2, "ca_keo": 4}
    },
    {
        "day": 4,
        "dishes": {"lau_mam": 1, "ca_loc_nuong_trui": 2, "goi_bong_sung": 1},
        "ingredients": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1, "ca_loc": 2, "bong_sung": 2}
    },
    {
        "day": 5,
        "dishes": {"lau_mam": 1, "lau_ca_linh_dien_dien": 1, "ca_loc_nuong_trui": 1},
        "ingredients": {"ca_linh": 5, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 2, "ca_loc": 1}
    }
]

SHOP_UPGRADES = {
    "oxygen": [
        {"level": 1, "price": 200, "oxygen_max_s": 45},
        {"level": 2, "price": 400, "oxygen_max_s": 60}
    ],
    "hp": [
        {"level": 1, "price": 250, "hp_max": 4},
        {"level": 2, "price": 500, "hp_max": 5}
    ]
}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, total_days=1):
        self.tuning = tuning
        self.scenario = scenario
        self.rng = streams
        self.ids = ids
        self.total_days = total_days

        day_scen = scenario.get("day", {})
        self.current_day = int(day_scen.get("day", 1))
        self.days_completed = 0
        self.money = int(day_scen.get("money", 0))
        self.earned = int(day_scen.get("earned", 0))
        self.reputation = float(day_scen.get("reputation", tuning.get("quan", {}).get("reputation_initial", 3.0)))

        # Nâng cấp đã mua và đang áp dụng
        self.upgrades = dict(day_scen.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)

        # Kế hoạch ngày
        self.day_plans = PRESET_DAY_PLANS
        self.current_plan = self._get_plan(self.current_day)

        self.phase = "gather"
        self.phase_tick = 0
        self.paused = False
        self.done = False
        self.reason = None

        # Kho nguyên liệu tích lũy và chuyển giao
        self.inventory_stock = {}

        # Trình mô phỏng buổi sáng hiện tại
        self._init_current_day()

    def _get_plan(self, day_num):
        for p in self.day_plans:
            if p["day"] == day_num:
                return p
        return self.day_plans[0]

    def _init_current_day(self):
        """Khởi tạo buổi sáng của ngày hiện tại với các nâng cấp active."""
        self.current_plan = self._get_plan(self.current_day)
        gather_tuning = dict(self.tuning.get("gather", {}))

        # Áp dụng nâng cấp
        if "oxygen" in self.active_upgrades:
            lvl = self.active_upgrades["oxygen"]
            if lvl == 1:
                gather_tuning["oxygen_max_s"] = 45
            elif lvl == 2:
                gather_tuning["oxygen_max_s"] = 60

        if "hp" in self.active_upgrades:
            lvl = self.active_upgrades["hp"]
            if lvl == 1:
                gather_tuning["hp_max"] = 4
            elif lvl == 2:
                gather_tuning["hp_max"] = 5

        effective_tuning = dict(self.tuning, gather=gather_tuning)
        gather_scenario = dict(self.scenario.get("gather", {}))
        gather_scenario["day"] = self.current_day

        self.sub_sim = GatherSim(effective_tuning, gather_scenario, self.rng, self.ids)
        self.phase = "gather"
        self.phase_tick = 0

    @property
    def time_left_ticks(self):
        if self.phase in ("gather", "quan") and hasattr(self, "sub_sim"):
            return self.sub_sim.time_left_ticks
        elif self.phase == "shop":
            return self.shop_time_left
        return 0

    def get_clock(self) -> dict:
        """Tính toán đồng hồ in-game 24H chuẩn:
        - 1 Ngày in-game 24H = 8 phút đời thực (480s = 28.800 ticks).
        - 1s đời thực = 3 phút in-game (1 tick = 3s in-game).
        - gather: 06:00 -> 15:00 (9h in-game = 540 phút game)
        - shop/prep: 15:00 -> 18:00 (3h in-game)
        - quan: 18:00 -> 23:00 (5h in-game = 300 phút game)
        - sleep/summary: 23:00 -> 06:00 (7h in-game)
        """
        if self.phase == "gather":
            sub_ticks = getattr(self.sub_sim, "ticks_run", self.phase_tick)
            tick_lim = getattr(self.sub_sim, "tick_limit", 10800)
            prog = min(1.0, sub_ticks / max(1, tick_lim))
            mins = 6 * 60 + int(prog * 540)
            period = "morning" if mins < 12 * 60 else "afternoon"
        elif self.phase == "quan":
            sub_ticks = getattr(self.sub_sim, "ticks_run", self.phase_tick)
            tick_lim = getattr(self.sub_sim, "tick_limit", 10800)
            prog = min(1.0, sub_ticks / max(1, tick_lim))
            mins = 18 * 60 + int(prog * 300)
            period = "evening"
        elif self.phase == "shop":
            prog = min(1.0, (600 - getattr(self, "shop_time_left", 600)) / 600.0)
            mins = 23 * 60 + int(prog * 60)
            period = "night"
        else:
            mins = 6 * 60
            period = "morning"

        hour = (mins // 60) % 24
        minute = mins % 60
        return {
            "hour": hour,
            "minute": minute,
            "time_str": f"{hour:02d}:{minute:02d}",
            "period": period,
            "real_minutes_per_24h": 8.0,
            "ratio_desc": "24h game = 8 phut doi thuc (1s thuc = 3 phut game)"
        }

    def get_areas(self) -> dict:
        """Trạng thái mở/đóng của 4 khu vực thế giới mở theo khung giờ in-game."""
        clk = self.get_clock()
        h = clk["hour"]
        return {
            "ben_lan": {
                "id": "ben_lan",
                "name": "Bến Lặn Sông Tiền",
                "open": 6 <= h < 15,
                "hours": "06:00 - 15:00",
                "desc": "Lặn bắt cá Linh, Cá Lóc, Cá Kèo và hái hoa"
            },
            "cho_chu_sau": {
                "id": "cho_chu_sau",
                "name": "Chợ Nổi Chú Sáu",
                "open": 15 <= h < 22,
                "hours": "15:00 - 22:00",
                "desc": "Mua bán nguyên liệu, nâng cấp ghe và trang bị"
            },
            "quan_an": {
                "id": "quan_an",
                "name": "Quán Ăn Má Tư",
                "open": 18 <= h < 23,
                "hours": "18:00 - 23:00",
                "desc": "Tiếp khách ghe, nấu nướng và phục vụ"
            },
            "ghe_nghi": {
                "id": "ghe_nghi",
                "name": "Ghe Nghỉ Út Sen",
                "open": (h >= 22 or h < 6),
                "hours": "22:00 - 06:00",
                "desc": "Nghỉ ngơi, hồi phục thể lực và sang ngày mới"
            }
        }

    def snapshot(self) -> dict:
        snap = {
            "day": self.current_day,
            "day_plan": self.current_plan,
            "upgrades": self.upgrades,
            "active_upgrades": self.active_upgrades,
            "days_completed": self.days_completed,
            "paused": self.paused,
            "clock": self.get_clock(),
            "areas": self.get_areas()
        }
        if self.phase in ("gather", "quan") and hasattr(self, "sub_sim"):
            snap.update(self.sub_sim.snapshot())
        elif self.phase == "shop":
            snap["stock"] = self.inventory_stock
            snap["shop_time_left"] = self.shop_time_left
        return snap

    def step(self, inp):
        events = []

        # 1. Cơ chế Tạm dừng (Pause / Resume)
        if inp.pressed("pause"):
            self.paused = not self.paused
            if self.paused:
                events.append(("paused", {}))
                return events
            else:
                events.append(("resumed", {}))

        if self.paused:
            return events

        # Bắt đầu ngày mới nếu ở đầu
        if self.phase_tick == 0 and self.phase == "gather":
            events.append(("day_start", {}))
            events.append(("day_plan", {
                "dishes": self.current_plan["dishes"],
                "ingredients": self.current_plan["ingredients"]
            }))
            events.append(("phase_start", {"phase": "gather"}))

        self.phase_tick += 1

        # 2. Xử lý theo Phase
        if self.phase == "gather":
            sub_evs = self.sub_sim.step(inp)
            events.extend(sub_evs)

            if self.sub_sim.done:
                # Bàn giao kho sang Quán
                self.inventory_stock = self.sub_sim.inventory_items()
                self.phase = "quan"
                self.phase_tick = 0
                events.append(("phase_start", {"phase": "quan"}))

                # Dựng Quán Sim
                quan_scenario = dict(self.scenario.get("quan", {}))
                quan_scenario["stock"] = self.inventory_stock
                quan_scenario["reputation"] = self.reputation
                quan_scenario["money"] = self.money
                quan_scenario["earned"] = self.earned

                # Lọc danh sách món theo kế hoạch ngày
                allowed = list(self.current_plan["dishes"].keys())
                self.sub_sim = QuanSim(self.tuning, quan_scenario, self.rng, self.ids,
                                      inventory=self.inventory_stock, allowed_dishes=allowed)

        elif self.phase == "quan":
            sub_evs = self.sub_sim.step(inp)
            events.extend(sub_evs)

            if self.sub_sim.done:
                # Cập nhật tiền và uy tín
                self.money = self.sub_sim.money
                self.earned = self.sub_sim.earned
                self.reputation = self.sub_sim.reputation

                # Chuyển sang Shop
                self.phase = "shop"
                self.phase_tick = 0
                self.shop_time_left = 600  # Shop mở tối đa 600 ticks (10s)
                events.append(("phase_start", {"phase": "shop"}))

        elif self.phase == "shop":
            self.shop_time_left -= 1

            # Xử lý buy trước
            if getattr(inp, "buy", None):
                buy_ev = self.buy_upgrade(inp.buy)
                events.append(buy_ev)

            # Xử lý lệnh mua / phím shop_done
            if inp.pressed("shop_done") or self.shop_time_left <= 0:
                reason = "done" if inp.pressed("shop_done") else "time"
                events.append(("shop_end", {"reason": reason}))
                self.days_completed += 1

                # Chốt nâng cấp đã mua sang active_upgrades
                self.active_upgrades = dict(self.upgrades)

                if self.days_completed >= self.total_days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    # Sang ngày kế tiếp
                    self.current_day += 1
                    self.inventory_stock = {}  # Kho dư bị bỏ sau shop
                    self._init_current_day()

        return events

    def inventory_items(self) -> dict:
        return dict(self.inventory_stock)

    def buy_upgrade(self, upgrade_id):
        """Mua nâng cấp tại Shop."""
        if self.phase != "shop":
            return ("buy_failed", {"action": upgrade_id, "reason": "not_in_shop"})

        if upgrade_id not in SHOP_UPGRADES:
            return ("buy_failed", {"action": upgrade_id, "reason": "unknown"})

        cur_lvl = self.upgrades.get(upgrade_id, 0)
        next_lvl = cur_lvl + 1

        up_list = SHOP_UPGRADES[upgrade_id]
        if next_lvl > len(up_list):
            return ("buy_failed", {"action": upgrade_id, "reason": "max_level"})

        info = up_list[next_lvl - 1]
        price = info["price"]
        if self.money < price:
            return ("buy_failed", {"action": upgrade_id, "reason": "funds"})

        self.money -= price
        self.upgrades[upgrade_id] = next_lvl
        return ("bought", {
            "upgrade": upgrade_id,
            "level": next_lvl,
            "price": price,
            "money": self.money
        })
