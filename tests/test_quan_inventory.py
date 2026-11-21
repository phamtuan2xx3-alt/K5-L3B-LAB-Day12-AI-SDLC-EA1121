"""Kiểm thử kho và menu độc lập với lịch khách và bước nấu."""

import unittest

from chonoi.contract import load_contract
from chonoi.runner import Session
from helpers import counts_tuning


class QuanInventory(unittest.TestCase):
    def make_sim(self, stock):
        tuning = counts_tuning()  # luật kho đếm (v1.0/1.1); v1.2 xem test_quan_freshness
        return Session("quan", tuning, {"stock": stock}, seed=1).sim

    def test_first_cookable_dish_reserves_without_changing_stock(self):
        stock = {"ca_loc": 1, "bong_sung": 2}
        sim = self.make_sim(stock)
        events = []
        dish, reservation = sim._choose_dish_for_customer(events)
        self.assertEqual(dish, "ca_loc_nuong_trui")
        self.assertEqual(reservation, {"ca_loc": 1})

        sim.customers.append({"id": "C1", "table_id": "T1", "dish": dish, "reserved": reservation})
        self.assertEqual(sim._choose_dish_for_customer(events), ("goi_bong_sung", {"bong_sung": 2}))
        self.assertEqual(sim.snapshot()["stock"], stock)
        self.assertEqual(events, [])

        sim.customers.clear()
        self.assertEqual(sim._choose_dish_for_customer(events), ("ca_loc_nuong_trui", {"ca_loc": 1}))

    def test_all_reservations_count_toward_no_dish(self):
        sim = self.make_sim({"bong_sung": 3, "ca_linh": 3})
        sim.customers = [{"reserved": {"bong_sung": 1}}, {"reserved": {"bong_sung": 1}}]
        events = []
        self.assertEqual(sim._get_available_stock(), {"bong_sung": 1, "ca_linh": 3})
        self.assertIsNone(sim._choose_dish_for_customer(events))
        self.assertEqual(events, [("no_dish", {})])

    def test_start_cooking_consumes_reservation_only_once(self):
        sim = self.make_sim({"ca_linh": 3, "bong_dien_dien": 1})
        dish, reservation = sim._choose_dish_for_customer([])
        customer = {"dish": dish, "reserved": reservation}
        sim.customers.append(customer)
        self.assertTrue(sim._consume_reservation(customer))
        self.assertEqual(customer["reserved"], {})
        self.assertEqual(sim.menu[dish]["recipe"], {"ca_linh": 3, "bong_dien_dien": 1})
        self.assertFalse(sim._consume_reservation(customer))
        self.assertEqual(sim.stock, {"ca_linh": 0, "bong_dien_dien": 0})

    def test_missing_ingredient_leaves_stock_and_reservation_intact(self):
        sim = self.make_sim({"ca_linh": 3})
        reservation = {"ca_linh": 3, "bong_dien_dien": 1}
        customer = {"reserved": dict(reservation)}
        self.assertFalse(sim._consume_reservation(customer))
        self.assertEqual(sim.stock, {"ca_linh": 3})
        self.assertEqual(customer["reserved"], reservation)
