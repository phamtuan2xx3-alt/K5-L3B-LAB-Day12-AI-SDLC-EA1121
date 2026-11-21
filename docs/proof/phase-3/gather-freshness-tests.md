# Bằng chứng Phase 3 — Lặn độ tươi (DEV 1, thanhtung578804)

Commit: Triển khai toàn diện hệ thống độ tươi trong giỏ lặn (`gather`), cấp cá thể ID, trừ hao 0.5/s, phát sự kiện `spoiled {location: "hold"}` và bàn giao kho cá thể.

## Kết quả chạy tests.test_gather_freshness -v
```
test_dung_30_uon_o_buoc_dau_phat_spoiled_mot_lan (tests.test_gather_freshness.GatherDecayAndSpoil.test_dung_30_uon_o_buoc_dau_phat_spoiled_mot_lan) ... ok
test_gio_lan_hao_05_moi_giay (tests.test_gather_freshness.GatherDecayAndSpoil.test_gio_lan_hao_05_moi_giay) ... ok
test_kep_day_0 (tests.test_gather_freshness.GatherDecayAndSpoil.test_kep_day_0) ... ok
test_sat_nguong_uon_dung_tick_va_theo_id (tests.test_gather_freshness.GatherDecayAndSpoil.test_sat_nguong_uon_dung_tick_va_theo_id) ... ok
test_catch_cap_id_va_fresh_100 (tests.test_gather_freshness.GatherHarvestAndCatchFreshness.test_catch_cap_id_va_fresh_100) ... ok
test_gather_end_inventory_handoff_itemized (tests.test_gather_freshness.GatherHarvestAndCatchFreshness.test_gather_end_inventory_handoff_itemized) ... ok
test_harvest_cap_id_va_fresh_100 (tests.test_gather_freshness.GatherHarvestAndCatchFreshness.test_harvest_cap_id_va_fresh_100) ... ok
test_monster_hit_drops_lifo_itemized (tests.test_gather_freshness.GatherMonsterHitAndFaintItemized.test_monster_hit_drops_lifo_itemized) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.010s

OK
```
