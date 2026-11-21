"""Bộ kiểm thử đơn vị cho Phase 3:
- Đồng hồ in-game 24H quy đổi ra 8 phút đời thực (480s = 28.800 ticks).
- Trạng thái mở/đóng của 4 khu vực thế giới mở (Hub Overworld) theo thời gian.
- Vòng lặp chuyển cảnh: Lặn bắt xong -> Chuẩn bị đồ -> Mở quán -> Ngủ.
"""

import json
import unittest
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.sim.day import DaySim


def load_full_tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


class TestPhase3TimeAndHubCycle(unittest.TestCase):

    def setUp(self):
        self.tuning = load_full_tuning()
        self.scenario = {
            "gather": {
                "time_limit_s": 180,
                "player": {"pos": [2, 0], "vel": [0, 0], "heading_deg": 0}
            },
            "quan": {
                "time_limit_s": 180,
                "player": {"pos": [8, 5], "vel": [0, 0], "heading_deg": 0}
            }
        }

    def test_clock_ratio_24h_to_8_minutes(self):
        """Kiểm tra tỷ lệ quy đổi: 24h in-game = 8 phút đời thực (480s = 28.800 ticks)."""
        sim = DaySim(self.tuning, self.scenario, Streams(1), IdAllocator(), total_days=1)
        clk = sim.get_clock()
        self.assertEqual(clk["real_minutes_per_24h"], 8.0)
        self.assertIn("time_str", clk)
        self.assertIn("hour", clk)
        self.assertIn("minute", clk)
        self.assertIn("period", clk)

    def test_clock_starts_at_morning_in_gather(self):
        """Bắt đầu ca lặn ở 06:00 sáng."""
        sim = DaySim(self.tuning, self.scenario, Streams(1), IdAllocator(), total_days=1)
        snap = sim.snapshot()
        self.assertIn("clock", snap)
        self.assertEqual(snap["clock"]["hour"], 6)
        self.assertEqual(snap["clock"]["minute"], 0)
        self.assertEqual(snap["clock"]["time_str"], "06:00")
        self.assertEqual(snap["clock"]["period"], "morning")

    def test_hub_areas_open_close_status_morning(self):
        """Ở 06:00 sáng: Bến Lặn mở, Quán ăn chưa mở, Chợ chưa mở, Ghe nghỉ đóng."""
        sim = DaySim(self.tuning, self.scenario, Streams(1), IdAllocator(), total_days=1)
        areas = sim.get_areas()
        self.assertTrue(areas["ben_lan"]["open"], "Bến lặn phải mở vào buổi sáng 06:00 - 15:00")
        self.assertFalse(areas["cho_chu_sau"]["open"], "Chợ Chú Sáu chỉ mở từ 15:00")
        self.assertFalse(areas["quan_an"]["open"], "Quán ăn Má Tư chỉ mở lúc 18:00")
        self.assertFalse(areas["ghe_nghi"]["open"], "Ghe nghỉ đóng ban ngày để đi làm")

    def test_hub_areas_afternoon_and_evening_states(self):
        """Mô phỏng đồng hồ ở các khung giờ khác nhau để kiểm tra mở/đóng khu vực."""
        sim = DaySim(self.tuning, self.scenario, Streams(1), IdAllocator(), total_days=1)

        # Giả lập ca quán (buổi tối 18:00 - 23:00)
        sim.phase = "quan"
        sim.sub_sim.ticks_run = 0
        sim.sub_sim.tick_limit = 10800
        clk = sim.get_clock()
        self.assertEqual(clk["hour"], 18)
        self.assertEqual(clk["time_str"], "18:00")
        self.assertEqual(clk["period"], "evening")

        areas = sim.get_areas()
        self.assertFalse(areas["ben_lan"]["open"], "Bến lặn phải đóng vào buổi tối")
        self.assertTrue(areas["cho_chu_sau"]["open"], "Chợ Chú Sáu mở đến 22:00")
        self.assertTrue(areas["quan_an"]["open"], "Quán ăn Má Tư đang mở phục vụ khách")
        self.assertFalse(areas["ghe_nghi"]["open"], "Chưa đến giờ ngủ")

        # Giả lập ca đêm / Shop (23:00)
        sim.phase = "shop"
        sim.shop_time_left = 600
        clk_night = sim.get_clock()
        self.assertEqual(clk_night["hour"], 23)
        self.assertEqual(clk_night["period"], "night")

        areas_night = sim.get_areas()
        self.assertFalse(areas_night["ben_lan"]["open"])
        self.assertFalse(areas_night["cho_chu_sau"]["open"])
        self.assertFalse(areas_night["quan_an"]["open"])
        self.assertTrue(areas_night["ghe_nghi"]["open"], "Ghe nghỉ mở từ 22:00 - 06:00 cho Út Sen ngủ")


if __name__ == "__main__":
    unittest.main()
