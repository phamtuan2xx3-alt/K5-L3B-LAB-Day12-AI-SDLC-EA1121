# Ma trận truy vết Phase 2 (TICKET-02 — Một ngày ở chợ nổi)

> Tag bàn giao: `phase-2`  
> Thời điểm xác thực: 21/11/2026  
> Trạng thái test suite: 64/64 test cases PASS (100%)  
> Smoke Integration: Đã lưu bằng chứng tại `docs/proof/phase-2/`

## 1. Bảng ma trận nghiệm thu (Acceptance Criteria Trace Matrix)

| AC | Nội dung yêu cầu | Cách kiểm chứng | Bằng chứng / File test | Kết quả |
| :---: | :--- | :--- | :--- | :---: |
| **AC-P2-01** | Test Contract v1.1: Chuẩn hóa tuning, 6 nguyên liệu (`ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`), 6 món ăn | `chonoi/contract.py`, `game.contract.json` | `tests/test_smoke_p1.py` & `tests/test_p2_quan_restaurant.py` | **ĐẠT** |
| **AC-P2-02** | Cá bơi tuần tra 1.5 m/s, đổi hướng mỗi 120 ticks theo seed, phản xạ mép $x \in [4, 96]$, sinh đàn cá định kỳ mỗi 360 ticks | `tests/test_p2_gather_movement_spawn.py` | `test_fish_swimming_movement`, `test_fish_boundary_bounce`, `test_fish_periodic_spawning` | **ĐẠT** |
| **AC-P2-03** | Thủy quái Cá Sấu Năm Chèo (M1, M2): tuần tra, phát hiện & rượt đuổi $\le 10$m, cắn $\le 1.5$m mất 1 HP & rơi $\lfloor\text{hold}/2\rfloor$ LIFO, recoil 60 ticks, ngất fainted khi 0 HP | `tests/test_p2_gather_movement_spawn.py` | `test_crocodile_patrol_to_chase_and_hit`, `test_crocodile_faint_on_zero_hp` | **ĐẠT** |
| **AC-P2-04** | Quán ăn 2 bếp (B1, B2), 4 bàn (T1..T4), 6 món, phục vụ & tính tiền, tip $20\%$ khi còn $\ge 50\%$ kiên nhẫn (+0.2 uy tín), khách bỏ về (-0.5 uy tín) | `tests/test_p2_quan_restaurant.py` | `test_customer_arrival_and_reserved_stock`, `test_kitchen_cooking_and_serving_cycle`, `test_customer_left_when_patience_expires` | **ĐẠT** |
| **AC-P2-05** | Chế độ `--mode day` (DayIntro $\to$ gather $\to$ EveningIntro $\to$ quan $\to$ DayResult $\to$ Shop $\to$ Ngày kế tiếp, 1..5 ngày), kế hoạch ngày D1..D5 của Má Tư | `chonoi/sim/day.py`, `chonoi/headless.py` | `tests/test_p2_day_mode_shop.py::test_day_mode_headless_cli_basic`, `test_multiday_completion_end_row` | **ĐẠT** |
| **AC-P2-06** | Shop và nâng cấp (bình oxy 45s/60s, áo phao 4/5 HP), lệnh `buy`, chốt nâng cấp và áp dụng từ Ngày kế tiếp | `tests/test_p2_day_mode_shop.py` | `test_shop_purchase_and_next_day_upgrade_applied`, `test_shop_buy_failed_funds_and_max_level` | **ĐẠT** |
| **AC-P2-07** | Cơ chế Tạm dừng / Tiếp tục (Pause/Resume via Esc/P), đóng băng sim, timer, snapshot `state: "paused"`, tiếp tục ngay khi resumed | `tests/test_p2_day_mode_shop.py` | `test_day_pause_and_resume` | **ĐẠT** |
| **AC-P2-08** | Smoke tích hợp luồng: `gather --inventory-out` $\to$ `quan --inventory` và `--mode day --days 1` | CLI headless | `docs/proof/phase-2/integration_inv.json`, `docs/proof/phase-2/integration_day.jsonl` | **ĐẠT** |
| **AC-P2-09** | Đồ họa Web Canvas 2.5D Dave the Diver Mekong mở rộng: Kèo Nèo N5/N6, Cá Kèo, Cá Sấu Năm Chèo, viền tím cảnh báo quái, HUD Shop modal, Pause modal | Trình duyệt `chonoi.live --mode gather` | `chonoi/web/index.html` | **ĐẠT** |

---

## 2. Ghi chú lý do cập nhật test suite cũ (Regression P1 với chuẩn Phase 2)

Theo hướng dẫn tại mục 1 và mục 5 trong `PHARSE2.md` (*"Thay số đã chọn ở Phase 1 bằng các giá trị chuẩn. Cập nhật cấu hình, spec và test cùng lúc. Ghi lý do nếu test cũ cần cập nhật vì luật mới"*):
1. **`test_con_03_old_and_future_modes_rejected`** (`tests/test_smoke_p1.py`):
   - *Lý do:* Ở Contract v1.0, `--mode day` được coi là future mode và bị từ chối với exit code 2. Ở Contract v1.1 (Phase 2), `--mode day` đã chính thức được hỗ trợ. Cập nhật bộ test từ chối các mode không hỗ trợ/cũ như `river` và `night`.
2. **`test_gather_snapshot_has_gather_fields`** (`tests/test_smoke_p1.py`):
   - *Lý do:* Ở Contract v1.0, `fish_initial` là danh sách 6 đàn cá cố định. Ở Contract v1.1, `fish_initial` là số nguyên `8` đàn cá sinh ngẫu nhiên theo seed từ 36 điểm sinh. Cập nhật kiểm tra số lượng cá khớp với `fish_initial` của tuning.
3. **`test_catch_partial_yield_fills_bag`** (`tests/test_dev2_harvest_catch.py`):
   - *Lý do:* Luật Phase 1 cho phép nhận một phần yield khi giỏ gần đầy (`min(y, space)`). Luật chuẩn Phase 2 quy định: *"Cần đủ chỗ cho cả đàn"*, nếu không đủ chỗ sẽ phát `hold_full` và cá không bị bắt. Cập nhật test case kiểm tra đúng theo luật Contract v1.1.

---

## 3. Bằng chứng kiểm thử tự động (Test Suite Summary)

```text
Ran 64 tests in 14.828s
OK
```

- `tests/test_dev2_harvest_catch.py`: 12/12 PASS
- `tests/test_p2_gather_movement_spawn.py`: 9/9 PASS
- `tests/test_p2_quan_restaurant.py`: 4/4 PASS
- `tests/test_p2_day_mode_shop.py`: 7/7 PASS
- `tests/test_smoke_p1.py`: 18/18 PASS
- `tests/test_python_starter_units.py`: 7/7 PASS
- `tests/test_live.py`: 1/1 PASS
- `tests/test_team_check.py`: 6/6 PASS
- `tools/check_team.py`: `OK: 5 thành viên: member1, phamtuan2xx3-alt, lekhanh2k5-dotcom, member4, moyymochi11`
