"""Kiểm thử tính năng sáng tạo: Cơ chế Áp suất dòng sâu Mekong (Depth Warning)."""

import json
import unittest

from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class BtnInput:
    def __init__(self, move=(0.0, 0.0), pressed_btn=None):
        self.move = move
        self._pressed = pressed_btn

    def pressed(self, btn):
        return self._pressed == btn


class TestDepthPressureInnovation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("game.contract.json", encoding="utf-8") as f:
            cls.tuning = json.load(f)["tuning"]

    def _make_sim(self, pos, oxygen_ticks=1000):
        scenario = {"player": {"pos": pos, "oxygen_ticks": oxygen_ticks}, "random_fish": False}
        return GatherSim(self.tuning, scenario, Streams(1), IdAllocator())

    def test_depth_warning_emitted_when_crossing_threshold(self):
        # Bắt đầu tại d = 17.5 (ngay sát ngưỡng 18.0)
        sim = self._make_sim([10.0, 17.5])
        self.assertFalse(sim.depth_warned)

        # Bơi chúc đầu xuống nước sâu
        all_events = []
        for _ in range(30):
            ev = sim.step(BtnInput(move=(0.0, 1.0)))
            all_events.extend(ev)

        # Kiểm tra đã vượt qua mốc d > 18.0
        self.assertGreater(sim.pos[1], 18.0)
        self.assertTrue(sim.depth_warned)

        # Sự kiện depth_warning phải được phát với thông số độ sâu
        warnings = [e for e in all_events if e[0] == "depth_warning"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("depth", warnings[0][1])
        self.assertGreaterEqual(warnings[0][1]["depth"], 18.0)

    def test_depth_warning_resets_when_surfacing_above_depth_zone(self):
        # Bắt đầu trong vùng nước sâu d = 20.0
        sim = self._make_sim([10.0, 20.0])
        sim.step(BtnInput())
        self.assertTrue(sim.depth_warned)

        # Bơi ngược lên vùng nước nông d < 18.0
        for _ in range(60):
            sim.step(BtnInput(move=(0.0, -1.0)))

        self.assertLess(sim.pos[1], 18.0)
        self.assertFalse(sim.depth_warned)

    def test_hyperbaric_oxygen_drain_in_depth_zone(self):
        # Ở nước nông d = 5.0: tiêu hao 1 tick oxy mỗi tick
        sim_shallow = self._make_sim([10.0, 5.0], oxygen_ticks=100)
        sim_shallow.step(BtnInput())
        self.assertEqual(sim_shallow.oxygen_ticks, 99)

        # Ở vùng sâu d = 20.0: tiêu hao 2 ticks oxy mỗi tick do áp suất
        sim_deep = self._make_sim([10.0, 20.0], oxygen_ticks=100)
        sim_deep.step(BtnInput())
        self.assertEqual(sim_deep.oxygen_ticks, 98)


if __name__ == "__main__":
    unittest.main()
