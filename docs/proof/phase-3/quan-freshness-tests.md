# Bằng chứng Phase 3 — Quán độ tươi (DEV 3, lekhanh2k5-dotcom)

Commit: `b37bb9f` trên nhánh `feat/quan-freshness` (tuning v1.2 dựng trong test vì `game.contract.json` chưa đổi sang 1.2).

## Toàn bộ test
```
Ran 125 tests in 15.753s
OK
```

## tests.test_quan_freshness -v
```
test_dung_30_uon_o_buoc_dau_phat_spoiled_mot_lan (tests.test_quan_freshness.DecayAndSpoil.test_dung_30_uon_o_buoc_dau_phat_spoiled_mot_lan) ... ok
test_kep_day_0 (tests.test_quan_freshness.DecayAndSpoil.test_kep_day_0) ... ok
test_kho_quan_hao_025_moi_giay_ke_ca_hang_dang_giu (tests.test_quan_freshness.DecayAndSpoil.test_kho_quan_hao_025_moi_giay_ke_ca_hang_dang_giu) ... ok
test_sat_nguong_uon_dung_tick_va_theo_id (tests.test_quan_freshness.DecayAndSpoil.test_sat_nguong_uon_dung_tick_va_theo_id) ... ok
test_bo_reserved_thi_cap_tuoi_nhat_theo_order_tick (tests.test_quan_freshness.FixtureV12.test_bo_reserved_thi_cap_tuoi_nhat_theo_order_tick) ... ok
test_giu_ca_the_khong_co (tests.test_quan_freshness.FixtureV12.test_giu_ca_the_khong_co) ... ok
test_giu_ca_the_uon (tests.test_quan_freshness.FixtureV12.test_giu_ca_the_uon) ... ok
test_giu_khac_cong_thuc (tests.test_quan_freshness.FixtureV12.test_giu_khac_cong_thuc) ... ok
test_hai_don_giu_chung_id (tests.test_quan_freshness.FixtureV12.test_hai_don_giu_chung_id) ... ok
test_scenario_stock_dem_bi_tu_choi_o_v12 (tests.test_quan_freshness.FixtureV12.test_scenario_stock_dem_bi_tu_choi_o_v12) ... ok
test_boa_tinh_tren_gia_da_chot (tests.test_quan_freshness.FreshPrice.test_boa_tinh_tren_gia_da_chot) ... ok
test_gia_chot_theo_trung_binh_fresh_sau_lan_hao_cua_buoc (tests.test_quan_freshness.FreshPrice.test_gia_chot_theo_trung_binh_fresh_sau_lan_hao_cua_buoc) ... ok
test_items_la_ca_the_sap_theo_kind_roi_id (tests.test_quan_freshness.FreshPrice.test_items_la_ca_the_sap_theo_kind_roi_id) ... ok
test_giu_lai_khong_du_thi_unfulfillable_khach_van_cho (tests.test_quan_freshness.HoldByIdAndRehold.test_giu_lai_khong_du_thi_unfulfillable_khach_van_cho) ... ok
test_hang_dang_giu_vua_uon_thi_nha_va_giu_lai (tests.test_quan_freshness.HoldByIdAndRehold.test_hang_dang_giu_vua_uon_thi_nha_va_giu_lai) ... ok
test_hang_uon_khong_dung_cho_khach_moi (tests.test_quan_freshness.HoldByIdAndRehold.test_hang_uon_khong_dung_cho_khach_moi) ... ok
test_khach_moi_giu_ca_the_tuoi_nhat_hoa_theo_id (tests.test_quan_freshness.HoldByIdAndRehold.test_khach_moi_giu_ca_the_tuoi_nhat_hoa_theo_id) ... ok
test_file_kho_dem_tra_ma_2_o_v12 (tests.test_quan_freshness.InventoryFileV12.test_file_kho_dem_tra_ma_2_o_v12) ... ok
test_ghi_doc_lai_chinh_xac_va_quan_nhan_nguyen_ven (tests.test_quan_freshness.InventoryFileV12.test_ghi_doc_lai_chinh_xac_va_quan_nhan_nguyen_ven) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.068s

OK
```
