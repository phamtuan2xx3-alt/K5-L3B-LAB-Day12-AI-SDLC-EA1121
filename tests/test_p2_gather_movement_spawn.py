"""Bộ unit test kiểm thử toàn diện cơ chế Phase 2 trong chonoi/sim/gather.py:
1. Nông sản mới Kèo Nèo (keo_neo) tại N5, N6.
2. Thủy sản mới Cá Kèo (ca_keo) yield 2.
3. Cá bơi tuần tra 1.5 m/s, dội mép sông, đổi hướng tại 120 ticks.
4. Sinh đàn cá định kỳ mỗi 360 ticks (fish_spawned).
5. Thủy quái Cá Sấu Năm Chèo (patrol, chase khi player gần, cắn táp mất 1 HP, rơi nửa giỏ LIFO, recoil 60 ticks).
6. Sinh tồn Oxy, Choke ngạt nước và ngất (faint).
"""

import math
import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def make_p2_tuning():
    return {
        "gather": {
            "duration_s": 180,
            "bounds": {"x": [0, 100], "d": [0, 30]},
            "dock_pos": [2, 0],
            "dock_radius": 3,
            "start_pos": [2, 0],
            "start_heading_deg": 0,
            "swim_speed": 4.0,
            "ramp_max_ticks": 6,
            "surface_depth": 0.5,
            "oxygen_max_s": 30,
            "oxygen_refill_per_tick": 6,
            "choke_interval_ticks": 60,
            "hp_max": 3,
            "hold_capacity": 12,
            "interact_radius": 2.0,
            "node_yield": 1,
            "regrow_s": 20,
            "catch_radius": 2.0,
            "catch_cooldown_s": 0.5,
            "fish_speed": 1.5,
            "fish_turn_ticks": 120,
            "fish_max": 12,
            "fish_spawn_ticks": 360,
            "fish_spawn_clearance": 1.0,
            "fish_x": [4, 96],
            "fish_yield": {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2},
            "nodes": [
                {"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]},
                {"id": "N3", "kind": "bong_sung", "pos": [44, 0]},
                {"id": "N5", "kind": "keo_neo", "pos": [76, 0]}
            ],
            "fish_initial": [
                {"id": "F1", "kind": "ca_linh", "pos": [15, 5], "heading_deg": 0},
                {"id": "F2", "kind": "ca_loc", "pos": [30, 10], "heading_deg": 0},
                {"id": "F3", "kind": "ca_keo", "pos": [45, 25], "heading_deg": 0}
            ],
            "monsters": {
                "spawns": [
                    {"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]], "from_day": 1}
                ]
            }
        },
        "quan": {"reputation_initial": 3.0}
    }


def make_inp(move=(0, 0), interact=False, catch=False):
    inp = LiveInputs()
    inp.set(list(move), interact=interact, catch=catch)
    return inp.advance()


class TestPhase2Gather(unittest.TestCase):

    def test_keo_neo_harvest(self):
        """Hái Kèo Nèo N5 tại mặt nước nhận 1 keo_neo vào giỏ."""
        tuning = make_p2_tuning()
        scenario = {"player": {"pos": [76.0, 0.0]}}
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        evs = sim.step(make_inp(interact=True))
        g_evs = [e for e in evs if e[0] == "gather"]
        self.assertEqual(len(g_evs), 1)
        self.assertEqual(g_evs[0][1]["kind"], "keo_neo")
        self.assertIn("keo_neo", sim.hold)

    def test_ca_keo_catch_yield_2(self):
        """Bắt Cá Kèo F3 yield 2 nhận 2 con vào giỏ."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [45.0, 25.0]},
            "fish": [{"id": "F3", "kind": "ca_keo", "pos": [45.0, 25.0], "heading_deg": 0}]
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        evs = sim.step(make_inp(catch=True))
        c_evs = [e for e in evs if e[0] == "fish_caught"]
        self.assertEqual(len(c_evs), 1)
        self.assertEqual(c_evs[0][1]["kind"], "ca_keo")
        self.assertEqual(sim.hold.count("ca_keo"), 2)

    def test_ca_keo_hold_full_if_not_enough_room_for_whole_school(self):
        """Phase 2: Bắt Cá Kèo (yield 2) khi giỏ 11/12 (chỉ còn 1 chỗ) -> hold_full, cá không bị bắt."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [45.0, 25.0]},
            "hold": ["ca_loc"] * 11,
            "fish": [{"id": "F3", "kind": "ca_keo", "pos": [45.0, 25.0], "heading_deg": 0}]
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        evs = sim.step(make_inp(catch=True))
        self.assertTrue(any(e[0] == "hold_full" for e in evs))
        self.assertFalse(any(e[0] == "fish_caught" for e in evs))
        self.assertTrue(any(f["id"] == "F3" for f in sim.fish))

    def test_fish_swimming_movement(self):
        """Cá bơi tuần tra với vận tốc 1.5 m/s sau 60 ticks di chuyển đúng 1.5m."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [2.0, 0.0]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50.0, 5.0], "heading_deg": 0.0, "age_ticks": 0}]
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        start_x = sim.fish[0]["pos"][0]
        # Chạy 60 ticks không có input
        for _ in range(60):
            sim.step(make_inp())

        end_x = sim.fish[0]["pos"][0]
        # 1.5 m/s trong 1s (60 ticks) hướng 0 độ (+x) -> x tăng 1.5m
        self.assertAlmostEqual(end_x - start_x, 1.5, places=3)

    def test_fish_boundary_bounce(self):
        """Cá bơi chạm mép x = 96 sẽ dội ngược lại."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [2.0, 0.0]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.99, 5.0], "heading_deg": 0.0, "age_ticks": 0}]
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        # Bước tiếp theo cá chạm mép 96 và dội lại
        sim.step(make_inp())
        f = sim.fish[0]
        self.assertLessEqual(f["pos"][0], 96.0)
        # Hướng bơi lật ngược sang trái (180 độ)
        self.assertAlmostEqual(f["heading_deg"], 180.0, places=1)

    def test_fish_periodic_spawning(self):
        """Sau 360 ticks, sim sinh thêm đàn cá mới và phát sự kiện fish_spawned."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [2.0, 0.0]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0], "heading_deg": 0.0}]
        }
        sim = GatherSim(tuning, scenario, Streams(42), IdAllocator())

        spawn_events = []
        for _ in range(360):
            evs = sim.step(make_inp())
            for e in evs:
                if e[0] == "fish_spawned":
                    spawn_events.append(e)

        self.assertEqual(len(spawn_events), 1)
        self.assertEqual(len(sim.fish), 2)

    def test_crocodile_patrol_to_chase_and_hit(self):
        """Cá Sấu Năm Chèo tuần tra -> rượt đuổi khi player d >= 10 và cách <= 10m -> táp mất 1 HP."""
        tuning = make_p2_tuning()
        # Đặt player tại [60.0, 20.0] (d >= 10, cách M1 [60.0, 24.0] 4.0m <= 10m)
        scenario = {
            "player": {"pos": [60.0, 20.0], "hp": 3},
            "hold": ["ca_loc", "ca_linh", "keo_neo", "bong_sung"],  # 4 món
            "monsters": [
                {"id": "M1", "kind": "ca_sau", "pos": [60.0, 21.0], "waypoints": [[60.0, 21.0], [64.0, 21.0]], "target_idx": 1}
            ]
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        # Khoảng cách 1.0m <= 1.5m -> Cá sấu cắn trúng!
        evs = sim.step(make_inp())
        hit_evs = [e for e in evs if e[0] == "monster_hit"]
        self.assertEqual(len(hit_evs), 1)
        # Mất 1 HP: 3 -> 2
        self.assertEqual(sim.hp, 2)
        # Rơi floor(4 / 2) = 2 món theo LIFO (bong_sung, keo_neo rơi trước)
        self.assertEqual(len(sim.hold), 2)
        self.assertEqual(sim.hold, ["ca_loc", "ca_linh"])
        # Player được bất tử 90 ticks
        self.assertEqual(sim.invuln_ticks, 90)
        # Cá Sấu vào recoil
        self.assertEqual(sim.monsters[0]["state"], "recoil")
        self.assertEqual(sim.monsters[0]["state_ticks_left"], 60)

    def test_crocodile_faint_on_zero_hp(self):
        """Cá Sấu táp khi player còn 1 HP -> faint, mất sạch giỏ, kết thúc ca fainted."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [60.0, 20.0], "hp": 1},
            "hold": ["ca_loc", "ca_linh"],
            "monsters": [
                {"id": "M1", "kind": "ca_sau", "pos": [60.0, 20.5], "waypoints": [[60.0, 20.5], [64.0, 20.5]]}
            ]
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        evs = sim.step(make_inp())
        self.assertEqual(sim.hp, 0)
        self.assertEqual(len(sim.hold), 0)
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "fainted")
        self.assertTrue(any(e[0] == "faint" for e in evs))

    def test_oxygen_depletion_and_choke(self):
        """Ở dưới nước không có oxy -> mất 1 Máu (choke) mỗi 60 ticks."""
        tuning = make_p2_tuning()
        scenario = {
            "player": {"pos": [20.0, 5.0], "hp": 3, "oxygen_ticks": 1}
        }
        sim = GatherSim(tuning, scenario, Streams(1), IdAllocator())

        # Tick 1: oxy 1 -> 0 phát oxygen_empty và choke ngay bước chạm 0
        evs1 = sim.step(make_inp())
        self.assertTrue(any(e[0] == "oxygen_empty" for e in evs1))
        self.assertTrue(any(e[0] == "choke" for e in evs1))
        self.assertEqual(sim.hp, 2)


if __name__ == "__main__":
    unittest.main()
