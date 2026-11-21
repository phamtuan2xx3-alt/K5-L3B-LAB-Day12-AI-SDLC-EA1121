# Bằng chứng lát 3 — khách quán (DEV 3, lekhanh2k5-dotcom)

Commit chạy: `bf059e4` trên nhánh `feat/quan-customers`.

## Toàn bộ test
```
Ran 50 tests in 12.689s
OK
```

## tests.test_quan_customers -v
```
python : test_chon_mon_tat_dinh_theo_seed (tests.test_quan_customers.Arrivals.test_chon_mon_tat_dinh_theo_seed) ... ok
At line:1 char:564
+ ... EAD; $out = python -m unittest tests.test_quan_customers -v 2>&1 | Ou ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (test_chon_mon_t...eo_seed) ... ok:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
test_het_ban_bo_luot_khong_event (tests.test_quan_customers.Arrivals.test_het_ban_bo_luot_khong_event) ... ok
test_khach_dau_tien_dung_first_customer_tick 
(tests.test_quan_customers.Arrivals.test_khach_dau_tien_dung_first_customer_tick) ... ok
test_kho_kha_dung_tru_phan_giu (tests.test_quan_customers.Arrivals.test_kho_kha_dung_tru_phan_giu) ... ok
test_kho_rong_phat_no_dish (tests.test_quan_customers.Arrivals.test_kho_rong_phat_no_dish) ... ok
test_random_customers_false_tat_khach_tu_sinh 
(tests.test_quan_customers.Arrivals.test_random_customers_false_tat_khach_tu_sinh) ... ok
test_assigned_khong_co_mon (tests.test_quan_customers.FixtureValidation.test_assigned_khong_co_mon) ... ok
test_eating_thieu_gia (tests.test_quan_customers.FixtureValidation.test_eating_thieu_gia) ... ok
test_giu_khac_cong_thuc (tests.test_quan_customers.FixtureValidation.test_giu_khac_cong_thuc) ... ok
test_giu_qua_ton (tests.test_quan_customers.FixtureValidation.test_giu_qua_ton) ... ok
test_kien_nhan_vuot_tran (tests.test_quan_customers.FixtureValidation.test_kien_nhan_vuot_tran) ... ok
test_truong_la (tests.test_quan_customers.FixtureValidation.test_truong_la) ... ok
test_hop_den_khach_den_va_mau_thuan_ma_2 (tests.test_quan_customers.Headless.test_hop_den_khach_den_va_mau_thuan_ma_2) 
... ok
test_an_xong_tra_tien_va_id_moi_noi_tiep 
(tests.test_quan_customers.PatienceAndLeaving.test_an_xong_tra_tien_va_id_moi_noi_tiep) ... ok
test_dong_ca_khach_cho_roi_closing_khong_tru_uy_tin 
(tests.test_quan_customers.PatienceAndLeaving.test_dong_ca_khach_cho_roi_closing_khong_tru_uy_tin) ... ok
test_het_kien_nhan_roi_tru_uy_tin_va_nha_giu_cho 
(tests.test_quan_customers.PatienceAndLeaving.test_het_kien_nhan_roi_tru_uy_tin_va_nha_giu_cho) ... ok
test_kien_nhan_giam_tu_buoc_sau (tests.test_quan_customers.PatienceAndLeaving.test_kien_nhan_giam_tu_buoc_sau) ... ok
test_roi_quan_bo_mon_cua_don_tren_tay 
(tests.test_quan_customers.PatienceAndLeaving.test_roi_quan_bo_mon_cua_don_tren_tay) ... ok

----------------------------------------------------------------------
Ran 18 tests in 0.652s

OK
```

