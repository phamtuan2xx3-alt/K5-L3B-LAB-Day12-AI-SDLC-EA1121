"""Buổi sáng — Lặn & Hái (`gather`).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Phase 1 & Phase 2 (Contract v1.0 & v1.1):
- Bơi + gia tốc ramp, kẹp mép sông (d không âm).
- Lặn / nổi: sự kiện dive / surface khi qua ngưỡng surface_depth (0.5m).
- Oxy & Ngạt: dưới nước trừ 1/tick, mặt nước hồi +6/tick. Hết oxy (oxygen_empty) thì ngạt (choke) mỗi 60 ticks mất 1 HP. Máu = 0 -> ngất (faint), mất toàn bộ giỏ đồ.
- Hái hoa: Bông Điên Điển, Bông Súng, Kèo Nèo tại d <= 0.5. Mọc lại sau 1200 ticks (node_regrown).
- Bắt cá: Cá Linh (yield 3), Cá Lóc (yield 1), Cá Kèo (yield 2) tại d > 0.5. Hồi chiêu 30 ticks.
- Cá bơi tuần tra: vận tốc 1.5 m/s, đổi hướng ở các mốc 120 ticks, dội mép sông.
- Sinh cá định kỳ: mỗi 360 ticks sinh đàn mới nếu còn dưới trần 12.
- Thủy quái Cá Sấu Năm Chèo (M1, M2): tuần tra 1.0 m/s -> rượt đuổi 3.0 m/s khi player gần. Táp mất 1 Máu, rơi floor(hold/2) LIFO, bất tử 90 ticks.
- Cập bến ghe thuyền (docked) hoặc hết giờ (time) kết thúc ca lặn.
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .freshness import config as freshness_config, frac, out_item
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")

SPAWN_X_LIST = [15, 30, 45, 60, 75, 90]
SPAWN_DEPTHS = {
    "ca_linh": [5, 10],
    "ca_loc": [10, 16],
    "ca_keo": [24, 27],
}
FISH_DEPTH_BOUNDS = {
    "ca_linh": [3, 12],
    "ca_loc": [8, 20],
    "ca_keo": [22, 28],
}


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.depth_warned = False  # sáng tạo: cảnh báo khi vừa vượt qua ngưỡng áp suất dòng sâu (d > 18)
        self.fresh = freshness_config(tuning)
        if self.fresh:
            raw_hold = scenario.get("hold", [])
            if isinstance(raw_hold, list) and raw_hold and isinstance(raw_hold[0], dict):
                self.hold = [dict(it, fresh=frac(it["fresh"])) for it in raw_hold]
                for it in self.hold:
                    self.ids.reserve(it["id"])
            elif isinstance(raw_hold, list):
                self.hold = []
                for k in raw_hold:
                    self.hold.append({"id": self.ids.new("I"), "kind": k, "fresh": self.fresh["initial"]})
            else:
                self.hold = []
        else:
            self.hold = list(scenario.get("hold", []))  # LIFO, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0

        # 1. Nút hoa (Nodes)
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        # 2. Đàn cá (Fish)
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = t["fish_initial"]
        else:
            src_fish = []

        if isinstance(src_fish, int):
            # Khởi tạo n đàn cá từ điểm sinh
            self.fish = self._init_random_fish(src_fish)
        else:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": float(f.get("heading_deg", 0.0)),
                          "age_ticks": int(f.get("age_ticks", 0))} for f in src_fish]

        # 3. Quái vật / Thủy quái (Monsters)
        if "monsters" in scenario:
            src_monsters = scenario["monsters"]
        elif "monsters" in t and "spawns" in t["monsters"]:
            current_day = scenario.get("day", 1)
            src_monsters = [m for m in t["monsters"]["spawns"] if m.get("from_day", 1) <= current_day]
        else:
            src_monsters = []

        self.monsters = []
        for m in src_monsters:
            wps = [[float(c) for c in wp] for wp in m.get("waypoints", [m["pos"], m["pos"]])]
            self.monsters.append({
                "id": m["id"],
                "kind": m.get("kind", "ca_sau"),
                "pos": [float(c) for c in m["pos"]],
                "waypoints": wps,
                "target_idx": int(m.get("target_idx", 1)),
                "state": m.get("state", "patrol"),
                "state_ticks_left": int(m.get("state_ticks_left", 0)),
                "recoil_dir": m.get("recoil_dir", None)
            })

        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])

        self.money = 0
        self.earned = 0
        self.reputation = tuning.get("quan", {}).get("reputation_initial", 3.0)
        self.done = False
        self.reason = None

    def _init_random_fish(self, count):
        # Sinh đàn ban đầu từ 36 điểm sinh theo seed
        rng = self.rng.get("fish_spawn")
        candidates = []
        for x in SPAWN_X_LIST:
            for kind, depths in SPAWN_DEPTHS.items():
                for d in depths:
                    candidates.append((kind, [float(x), float(d)]))
        rng.shuffle(candidates)
        selected = candidates[:min(count, len(candidates))]
        fish_list = []
        for i, (kind, pos) in enumerate(selected):
            fid = f"F{i+1}"
            heading = float(rng.randint(0, 359))
            fish_list.append({"id": fid, "kind": kind, "pos": pos, "heading_deg": heading, "age_ticks": 0})
        return fish_list

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self):
        if self.fresh:
            return [out_item(it) for it in sort_by_id(self.hold)]
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        snap = {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [out_item(it) for it in self.hold] if self.fresh else self.hold,
            "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
        }
        if self.monsters:
            snap["monsters"] = [{"id": m["id"], "kind": m["kind"], "pos": m["pos"],
                                 "state": m["state"], "target_idx": m["target_idx"]}
                                for m in sort_by_id(self.monsters)]
        return snap

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        self.phase_tick += 1

        # 1. Đồng hồ, cooldown, giảm bất tử, hồi nút
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        # 1b. v1.2: Hao tươi giỏ lặn, phát spoiled theo id khi fresh đi từ >= 30 xuống < 30
        if self.fresh:
            thr, step_decay = self.fresh["spoiled_below"], self.fresh["gather_decay"]
            for it in sort_by_id(self.hold):
                before = it["fresh"]
                it["fresh"] = max(Fraction(0), before - step_decay)
                if before >= thr > it["fresh"]:
                    events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

        # 2. Bơi + chặn mép
        prev_surface = self._at_surface()
        self._move(inp)
        cur_surface = self._at_surface()

        # Dive / surface event
        if prev_surface and not cur_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not prev_surface and cur_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        # Cảnh báo áp suất dòng sâu (d > 18.0)
        if self.pos[1] > 18.0:
            if not self.depth_warned:
                self.depth_warned = True
                events.append(("depth_warning", {"depth": self.pos[1]}))
        else:
            self.depth_warned = False

        # 3. Oxy, Ngạt, Máu & Ngất
        refill_rate = self.t.get("oxygen_refill_per_tick", 6)
        if cur_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill_rate)
            self.zero_oxy_ticks = 0
        else:
            drain = 2 if self.pos[1] > 18.0 else 1
            if self.oxygen_ticks > 0:
                self.oxygen_ticks = max(0, self.oxygen_ticks - drain)
                if self.oxygen_ticks == 0:
                    events.append(("oxygen_empty", {}))
                    self.zero_oxy_ticks = 0

            if self.oxygen_ticks == 0:
                choke_interval = self.t.get("choke_interval_ticks", 60)
                if self.zero_oxy_ticks % choke_interval == 0:
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = list(self.hold)
                        self.hold = []
                        events.append(("faint", {
                            "cause": "oxygen",
                            "lost": [out_item(it) for it in lost] if self.fresh else lost,
                            "hp": 0
                        }))
                        self._finish("fainted", events)
                        return events
                self.zero_oxy_ticks += 1

        # 4. Thủy quái (Cá Sấu Năm Chèo) & Hit detection
        if self.monsters:
            self._step_monsters(events)
            if self.done:
                return events

        # 5. Tương tác (bến trước, rồi hái)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            self._step_harvest(events)

        # 6. Bắt cá theo vị trí trước khi cá bơi
        if inp.pressed("catch"):
            self._step_catch(events)

        # 7. Xét hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 8. Nếu còn giờ: cá bơi tuần tra & sinh thêm cá theo lịch
        if self.t.get("fish_speed"):
            self._step_fish_movement()
            self._step_fish_spawning(events)

        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    # --- DEV 2: Hái hoa mặt nước ------------------------------------------------
    def _step_harvest(self, events):
        """Hái hoa tại mặt nước (d <= surface_depth), tie-breaking id_key tự nhiên."""
        if not self._at_surface():
            return
        cands = [n for n in self.nodes if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]]
        if not cands:
            return
        cands.sort(key=lambda n: (round(math.dist(self.pos, n["pos"]), 6), id_key(n["id"])))
        chosen = cands[0]
        capacity = self.t["hold_capacity"]
        if len(self.hold) >= capacity:
            events.append(("hold_full", {}))
            return
        yield_n = self.t.get("node_yield", 1)
        space = capacity - len(self.hold)
        add_n = min(yield_n, space)
        if self.fresh:
            for _ in range(add_n):
                iid = self.ids.new("I")
                self.hold.append({"id": iid, "kind": chosen["kind"], "fresh": self.fresh["initial"]})
        else:
            self.hold.extend([chosen["kind"]] * add_n)
        chosen["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
        events.append(("gather", {"node_id": chosen["id"], "kind": chosen["kind"]}))

    # --- DEV 2: Săn bắt cá dưới lòng sông ---------------------------------------
    def _step_catch(self, events):
        """Bắt cá dưới nước (d > surface_depth), cooldown 30 ticks, tie-breaking id_key."""
        if self._at_surface() or self.catch_cd_ticks > 0:
            return
        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
        cands = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]]
        if not cands:
            return  # Quăng hụt: vẫn mất hồi chiêu 30 ticks
        cands.sort(key=lambda f: (round(math.dist(self.pos, f["pos"]), 6), id_key(f["id"])))
        chosen = cands[0]
        capacity = self.t["hold_capacity"]

        y = self.t["fish_yield"].get(chosen["kind"], 1)
        space = capacity - len(self.hold)

        # Quy tắc Phase 2: Cần đủ chỗ cho cả đàn; nếu thiếu bắn hold_full và cá không bị mất
        if self.t.get("fish_speed") and space < y:
            events.append(("hold_full", {}))
            return

        if len(self.hold) >= capacity:
            events.append(("hold_full", {}))
            return

        add_n = min(y, space)
        if self.fresh:
            for _ in range(add_n):
                iid = self.ids.new("I")
                self.hold.append({"id": iid, "kind": chosen["kind"], "fresh": self.fresh["initial"]})
        else:
            self.hold.extend([chosen["kind"]] * add_n)
        self.fish = [f for f in self.fish if f["id"] != chosen["id"]]
        events.append(("fish_caught", {"fish_id": chosen["id"], "kind": chosen["kind"]}))

    # --- DEV 2: Cá bơi tuần tra (Phase 2) ---------------------------------------
    def _step_fish_movement(self):
        speed = float(self.t.get("fish_speed", 1.5))
        dist_per_tick = speed / TICK
        turn_interval = int(self.t.get("fish_turn_ticks", 120))
        bounds_x = self.t.get("fish_x", [4, 96])

        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            # Đổi hướng theo seed ở bước bơi thứ 120, 240... trước khi di chuyển
            if f["age_ticks"] % turn_interval == 0:
                rng = self.rng.get(f"fish_turn_{f['id']}")
                f["heading_deg"] = float(rng.randint(0, 359))

            rad = math.radians(f["heading_deg"])
            vx = dist_per_tick * math.cos(rad)
            vd = dist_per_tick * math.sin(rad)

            f["pos"][0] += vx
            f["pos"][1] += vd

            # Phản xạ mép x
            if f["pos"][0] < bounds_x[0]:
                f["pos"][0] = bounds_x[0] + (bounds_x[0] - f["pos"][0])
                vx = -vx
            elif f["pos"][0] > bounds_x[1]:
                f["pos"][0] = bounds_x[1] - (f["pos"][0] - bounds_x[1])
                vx = -vx

            # Phản xạ mép d theo tầng nước của loài
            depth_bounds = FISH_DEPTH_BOUNDS.get(f["kind"], [5, 20])
            if f["pos"][1] < depth_bounds[0]:
                f["pos"][1] = depth_bounds[0] + (depth_bounds[0] - f["pos"][1])
                vd = -vd
            elif f["pos"][1] > depth_bounds[1]:
                f["pos"][1] = depth_bounds[1] - (f["pos"][1] - depth_bounds[1])
                vd = -vd

            f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360

    # --- DEV 2: Sinh cá theo lịch (Phase 2) -------------------------------------
    def _step_fish_spawning(self, events):
        spawn_interval = int(self.t.get("fish_spawn_ticks", 360))
        if self.phase_tick % spawn_interval != 0 or len(self.fish) >= int(self.t.get("fish_max", 12)):
            return

        clearance = float(self.t.get("fish_spawn_clearance", 1.0))
        # Tìm các điểm sinh hợp lệ (cách mọi đàn đang sống > clearance)
        valid_points = []
        for x in SPAWN_X_LIST:
            for kind, depths in SPAWN_DEPTHS.items():
                for d in depths:
                    pt = [float(x), float(d)]
                    if all(math.dist(pt, f["pos"]) > clearance for f in self.fish):
                        valid_points.append((kind, pt))

        if not valid_points:
            return

        # Phân bổ trọng số theo các loài còn điểm hợp lệ
        weights_map = {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3}
        available_kinds = sorted(list(set(k for k, _ in valid_points)))
        total_w = sum(weights_map[k] for k in available_kinds)
        normalized_w = [weights_map[k] / total_w for k in available_kinds]

        rng = self.rng.get("fish_spawn")
        r = rng.random()
        cum = 0.0
        chosen_kind = available_kinds[-1]
        for k, w in zip(available_kinds, normalized_w):
            cum += w
            if r <= cum:
                chosen_kind = k
                break

        # Chọn đều một điểm sinh của loài đó
        kind_points = [pt for k, pt in valid_points if k == chosen_kind]
        chosen_pt = kind_points[rng.randint(0, len(kind_points) - 1)]

        new_id = self.ids.new("F")
        init_heading = float(rng.randint(0, 359))
        new_fish = {
            "id": new_id,
            "kind": chosen_kind,
            "pos": list(chosen_pt),
            "heading_deg": init_heading,
            "age_ticks": 0
        }
        self.fish.append(new_fish)
        events.append(("fish_spawned", {"id": new_id, "kind": chosen_kind, "pos": list(chosen_pt)}))

    # --- DEV 1: Cá Sấu Năm Chèo (Phase 2 Monsters) ------------------------------
    def _step_monsters(self, events):
        player_d = self.pos[1]
        for m in sort_by_id(self.monsters):
            # Recoil state
            if m["state"] == "recoil":
                if m["state_ticks_left"] > 0:
                    r_dir = m.get("recoil_dir") or [1.0, 0.0]
                    # lùi 2/60 m mỗi bước
                    m["pos"][0] += r_dir[0] * (2.0 / 60.0)
                    m["pos"][1] += r_dir[1] * (2.0 / 60.0)
                    # Chặn mép x in [0, 100], d in [10, 30]
                    m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
                    m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))
                    m["state_ticks_left"] -= 1
                    if m["state_ticks_left"] <= 0:
                        m["state"] = "patrol"
                continue

            dist_p = math.dist(m["pos"], self.pos)

            # State transition: patrol <-> chase
            if m["state"] == "patrol":
                if player_d >= 10.0 and dist_p <= 10.0:
                    m["state"] = "chase"
            elif m["state"] == "chase":
                if player_d < 10.0 or dist_p > 16.0:
                    m["state"] = "patrol"

            # Di chuyển theo state
            if m["state"] == "chase":
                # Bơi về phía người chơi ở 3.0 m/s
                v = 3.0 / TICK
                angle = math.atan2(self.pos[1] - m["pos"][1], self.pos[0] - m["pos"][0])
                m["pos"][0] += v * math.cos(angle)
                m["pos"][1] += v * math.sin(angle)
            else:
                # Patrol: 1.0 m/s tới waypoint mục tiêu
                v = 1.0 / TICK
                target_wp = m["waypoints"][m["target_idx"]]
                d_to_wp = math.dist(m["pos"], target_wp)
                if d_to_wp <= v:
                    m["pos"] = list(target_wp)
                    m["target_idx"] = 1 - m["target_idx"]
                else:
                    angle = math.atan2(target_wp[1] - m["pos"][1], target_wp[0] - m["pos"][0])
                    m["pos"][0] += v * math.cos(angle)
                    m["pos"][1] += v * math.sin(angle)

            # Chặn mép x in [0, 100], d in [10, 30]
            m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
            m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))

        # Hit detection sau khi cả hai di chuyển
        if player_d >= 10.0 and self.invuln_ticks == 0:
            hits = [m for m in self.monsters if m["state"] != "recoil" and math.dist(m["pos"], self.pos) <= 1.5]
            if hits:
                hits.sort(key=lambda m: (round(math.dist(m["pos"], self.pos), 6), id_key(m["id"])))
                hit_m = hits[0]
                self.hp -= 1
                drop_n = len(self.hold) // 2
                lost = [self.hold.pop() for _ in range(drop_n)]  # LIFO
                self.invuln_ticks = 90

                # Cá Sấu vào recoil 60 bước lùi xa người chơi
                dx = hit_m["pos"][0] - self.pos[0]
                dd = hit_m["pos"][1] - self.pos[1]
                mag = math.hypot(dx, dd)
                if mag < 1e-6:
                    recoil_dir = [1.0, 0.0]
                else:
                    recoil_dir = [dx / mag, dd / mag]

                hit_m["state"] = "recoil"
                hit_m["state_ticks_left"] = 60
                hit_m["recoil_dir"] = recoil_dir

                events.append(("monster_hit", {
                    "monster_id": hit_m["id"],
                    "hp": self.hp,
                    "lost": [out_item(it) for it in lost] if self.fresh else lost,
                    "pos": list(self.pos)
                }))

                if self.hp <= 0:
                    lost_remaining = list(self.hold)
                    self.hold = []
                    events.append(("faint", {
                        "cause": "monster",
                        "lost": [out_item(it) for it in lost_remaining] if self.fresh else lost_remaining,
                        "hp": 0
                    }))
                    self._finish("fainted", events)

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
