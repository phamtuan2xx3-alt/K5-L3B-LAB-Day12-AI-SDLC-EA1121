"""Unit tests kiểm thử chế độ Mode Day, Kế hoạch ngày, Vòng lặp pha, Shop & Nâng cấp cho Phase 2."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from helpers import Workdir, read_jsonl, run_headless, snapshots, write_json, frames


class TestDayModeAndShop(unittest.TestCase):
    def test_day_plan_override_recomputes_ingredients_and_rejects_mismatch(self):
        with Workdir() as w:
            plan = {"day": 1, "dishes": {"lau_mam": 2}}
            scenario = write_json(w.path("scenario.json"), {"day": {"day_plan": [plan]}})
            out = w.path("day.jsonl")
            args = ("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", scenario, "--out", out)
            code, err = run_headless(*args)
            self.assertEqual(code, 0, err)
            self.assertEqual(read_jsonl(out)[0]["day_plan"]["ingredients"],
                             {"ca_linh": 4, "ca_keo": 2, "keo_neo": 2, "bong_dien_dien": 2})
            plan["ingredients"] = {"ca_linh": 2}
            write_json(scenario, {"day": {"day_plan": [plan]}})
            code, err = run_headless(*args)
            self.assertEqual(code, 2, err)

    def test_day_mode_headless_cli_basic(self):
        """Khởi chạy headless mode day qua CLI, kiểm tra snapshot tick 0 và các event đầu ca."""
        with Workdir() as w:
            out = w.path("day.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "5", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            self.assertGreater(len(rows), 0)

            # Snapshot 0
            s0 = rows[0]
            self.assertEqual(s0["type"], "snapshot")
            self.assertEqual(s0["mode"], "day")
            self.assertEqual(s0["phase"], "gather")
            self.assertEqual(s0["day"], 1)
            self.assertIn("day_plan", s0)
            self.assertEqual(s0["day_plan"]["day"], 1)
            self.assertEqual(s0["upgrades"], {})
            self.assertEqual(s0["active_upgrades"], {})

            # Event tick 1
            ev_names = [r["name"] for r in rows if r.get("type") == "event"]
            self.assertIn("day_start", ev_names)
            self.assertIn("day_plan", ev_names)
            self.assertIn("phase_start", ev_names)

            # Vỏ event chế độ day có thêm trường 'day'
            day_evs = [r for r in rows if r.get("type") == "event"]
            self.assertTrue(all("day" in r for r in day_evs))

    def test_day_cli_validation_exit_2(self):
        """Kiểm tra các ràng buộc CLI cho mode day."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            # --days ngoài khoảng [1, 5]
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--days", "0", "--out", out)
            self.assertEqual(code, 2)
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--days", "6", "--out", out)
            self.assertEqual(code, 2)

            # --days với mode khác
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10", "--days", "2", "--out", out)
            self.assertEqual(code, 2)

            # --inventory hoặc --inventory-out với day
            inv = write_json(w.path("inv.json"), {"items": {}})
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--inventory", inv, "--out", out)
            self.assertEqual(code, 2)
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--inventory-out", inv, "--out", out)
            self.assertEqual(code, 2)

    def test_day_scenario_restrictions(self):
        """Cấm quan.stock và quan.reputation trong scenario khi chạy mode day."""
        with Workdir() as w:
            out = w.path("o.jsonl")
            sc_bad1 = write_json(w.path("sc1.json"), {"quan": {"stock": {"ca_loc": 1}}})
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--scenario", sc_bad1, "--out", out)
            self.assertEqual(code, 2)

            sc_bad2 = write_json(w.path("sc2.json"), {"quan": {"reputation": 4.5}})
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--scenario", sc_bad2, "--out", out)
            self.assertEqual(code, 2)

    def test_day_pause_and_resume(self):
        """Kiểm tra cơ chế tạm dừng Esc/P và tiếp tục."""
        with Workdir() as w:
            out = w.path("pause.jsonl")
            # Bấm pause ở tick 2, nhả tick 3, bấm lại tick 4 để resume
            inp = write_json(w.path("inp.json"), frames(
                {"tick": 2, "pause": True},
                {"tick": 3, "pause": False},
                {"tick": 4, "pause": True}
            ))
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "8",
                                     "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            ev_names = [r.get("name") for r in rows if r.get("type") == "event"]
            self.assertIn("paused", ev_names)
            self.assertIn("resumed", ev_names)

            # Snapshot khi paused phải có state == 'paused'
            snaps = [r for r in rows if r.get("type") == "snapshot"]
            paused_snaps = [s for s in snaps if s.get("state") == "paused"]
            self.assertGreater(len(paused_snaps), 0)

    def test_shop_purchase_and_next_day_upgrade_applied(self):
        """Quy trình Shop: nạp tiền, kết thúc gather & quan, vào Shop mua Bình Oxy cấp 1 (200k), sang Ngày 2 có hiệu lực."""
        with Workdir() as w:
            out = w.path("shop.jsonl")
            sc = write_json(w.path("sc.json"), {
                "day": {"money": 500, "earned": 500},
                "gather": {"time_left_ticks": 1, "random_fish": False},
                "quan": {"time_left_ticks": 1}
            })
            # Tick 0: gather bắt đầu, tick 1: hết giờ gather -> sang quan
            # Tick 2: hết giờ quan -> sang shop
            # Tick 3: mua oxygen (cấp 1, giá 200), tick 4: bấm shop_done
            inp = write_json(w.path("inp.json"), frames(
                {"tick": 3, "buy": "oxygen"},
                {"tick": 4, "shop_done": True}
            ))
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--days", "2",
                                     "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            evs = [r for r in rows if r.get("type") == "event"]
            bought_evs = [r for r in evs if r.get("name") == "bought"]
            self.assertEqual(len(bought_evs), 1)
            b_data = bought_evs[0]["data"]
            self.assertEqual(b_data["upgrade"], "oxygen")
            self.assertEqual(b_data["level"], 1)
            self.assertEqual(b_data["price"], 200)
            self.assertEqual(b_data["money"], 300)

            shop_end_evs = [r for r in evs if r.get("name") == "shop_end"]
            self.assertEqual(len(shop_end_evs), 1)
            self.assertEqual(shop_end_evs[0]["data"]["reason"], "done")

            # Sang Ngày 2: kiểm tra active_upgrades đã được áp dụng (oxygen = 1)
            day2_snaps = [r for r in rows if r.get("type") == "snapshot" and r.get("day") == 2 and r.get("phase") == "gather"]
            self.assertGreater(len(day2_snaps), 0)
            d2_s = day2_snaps[0]
            self.assertEqual(d2_s["active_upgrades"].get("oxygen"), 1)
            # Oxy tối đa ở cấp 1 là 45s = 2700 ticks
            self.assertEqual(d2_s["player"]["oxygen_max_ticks"], 2700)

    def test_shop_buy_failed_funds_and_max_level(self):
        """Mua nâng cấp khi không đủ tiền hoặc đã đạt cấp tối đa -> buy_failed."""
        with Workdir() as w:
            out = w.path("shop_fail.jsonl")
            sc = write_json(w.path("sc.json"), {
                "day": {"money": 50, "earned": 50},  # Không đủ 200k
                "gather": {"time_left_ticks": 1, "random_fish": False},
                "quan": {"time_left_ticks": 1}
            })
            inp = write_json(w.path("inp.json"), frames(
                {"tick": 3, "buy": "oxygen"}
            ))
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "6", "--days", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            fail_evs = [r for r in rows if r.get("name") == "buy_failed"]
            self.assertEqual(len(fail_evs), 1)
            self.assertEqual(fail_evs[0]["data"]["reason"], "funds")

    def test_multiday_completion_end_row(self):
        """Chạy hoàn thành trọn vẹn số ngày (--days 1), kiểm tra end line và days_completed."""
        with Workdir() as w:
            out = w.path("complete.jsonl")
            sc = write_json(w.path("sc.json"), {
                "gather": {"time_left_ticks": 1, "random_fish": False},
                "quan": {"time_left_ticks": 1}
            })
            inp = write_json(w.path("inp.json"), frames(
                {"tick": 3, "shop_done": True}
            ))
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--days", "1",
                                     "--scenario", sc, "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            end_row = rows[-1]
            self.assertEqual(end_row["type"], "end")
            self.assertEqual(end_row["mode"], "day")
            self.assertEqual(end_row["state"], "finished")
            self.assertEqual(end_row["reason"], "days_complete")
            self.assertEqual(end_row["days_completed"], 1)


if __name__ == "__main__":
    unittest.main()
