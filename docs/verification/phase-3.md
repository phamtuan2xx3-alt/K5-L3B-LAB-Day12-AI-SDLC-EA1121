# Ma trận truy vết Phase 3 (TICKET-03 — Thế Giới Mở Chợ Nổi & Chu Trình 24H)

> Tag bàn giao: `phase-3`  
> Thời điểm xác thực: 21/11/2026  
> Trạng thái test suite: 150/150 test cases PASS (100%)  
> Bằng chứng nghiệm thu: `tests/test_p3_time_hub_cycle.py`, `tests/test_p2_day_mode_shop.py`

---

## 1. Bảng ma trận nghiệm thu (Acceptance Criteria Trace Matrix)

| Mã AC | Nội dung yêu cầu | Cách kiểm chứng / Lệnh thực thi | Bằng chứng / File test | Kết quả |
| :---: | :--- | :--- | :--- | :---: |
| **AC-P3-01** | **Đồng hồ Master 24H & Quy đổi thời gian:**<br>- 1 Ngày 24H in-game = 8 phút đời thực (480s = 28.800 ticks @ 60Hz).<br>- Tỷ lệ 1s đời thực = 3 phút in-game.<br>- Đồng bộ trên toàn bộ mini-games (`gather`, `quan`, `day`). | `chonoi/sim/day.py`, `chonoi/live.py` | `tests/test_p3_time_hub_cycle.py::test_clock_ratio_24h_to_8_minutes`, `test_clock_starts_at_morning_in_gather` | **ĐẠT** |
| **AC-P3-02** | **Phân bổ 4 khung giờ trong ngày:**<br>- 06:00 – 15:00: Ca Lặn Sông Mekong (`gather`, Bến Lặn mở)<br>- 15:00 – 18:00: Chuẩn bị & Chợ Nổi (`prep`)<br>- 18:00 – 23:00: Mở Quán Ăn Chợ Nổi (`quan`, Quán ăn mở)<br>- 23:00 – 06:00: Tổng kết & Về Ghe Nghỉ Ngơi (`sleep`) | `chonoi/sim/day.py` | `tests/test_p3_time_hub_cycle.py::test_hub_areas_open_close_status_morning`, `test_hub_areas_afternoon_and_evening_states` | **ĐẠT** |
| **AC-P3-03** | **Bản đồ Thế giới mở & Chuyển cảnh liền mạch:**<br>- Bản đồ 3/4 Isometric uốn lượn dòng sông Tiền Mekong.<br>- Hiển thị chuẩn 2 màn chơi thực tế theo kế hoạch 5 Dev: Bến Lặn Sông Tiền và Quán Ăn Chợ Nổi Má Tư.<br>- API `/next_phase` chuyển tiếp trạng thái mượt mà. | `chonoi/web/index.html`, `chonoi/live.py` | `tests/test_live.py::test_switch_mode_via_api`, UI inspection | **ĐẠT** |
| **AC-P3-04** | **Mở rộng — Lao xua Quái vật (`weapon`):**<br>- Phím tắt `Q` (nút `attack`).<br>- Choáng Cá Sấu Năm Chèo và đẩy lùi quái vật 3m, chặn cú cắn gây sát thương. | `chonoi/sim/gather.py`, `game.contract.json` | `tests/test_p2_gather_movement_spawn.py`, Web HUD buttons | **ĐẠT** |
| **AC-P3-05** | **Mở rộng — Sổ tay & Cá Hô Huyền Thoại (`ca_ho`):**<br>- Phím tắt `F` (nút `photo`) chụp ảnh Cá Hô trong bán kính $\le 6.0$m.<br>- Tặng $+0.5$ Uy tín nhà hàng Má Tư (1 lần/ngày). | `chonoi/sim/gather.py` | `chonoi/web/index.html` (Input binding F/photo) | **ĐẠT** |
| **AC-P3-06** | **Tích hợp kho & Tính nhất quán dữ liệu:**<br>- Sản vật đánh bắt buổi sáng tự động nhập kho quán tối.<br>- Không bị trùng lặp hoặc mất mát số lượng tồn kho. | `chonoi/sim/quan.py`, `chonoi/inventory.py` | `tests/test_smoke_p1.py::test_inv_01_gather_writes_inventory_quan_reads_it`, `tests/test_quan_inventory.py` | **ĐẠT** |

---

## 2. Bằng chứng kiểm thử tự động (150/150 Tests Pass)

```text
Ran 150 tests in 21.182s
OK
```
