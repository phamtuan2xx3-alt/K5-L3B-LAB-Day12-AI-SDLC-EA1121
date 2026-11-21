# Ma trận truy vết Phase 4 (TICKET-04 — Phát hành v1.0.0)

> Tag bàn giao: `phase-4` = GitHub Release `v1.0.1` (commit `c214a21`; bản sửa của `v1.0.0`, xem AC-P4-07)  
> Test Contract: `v1.3`  
> Trạng thái test suite: 150/150 test cases PASS (100%)  
> Bằng chứng nghiệm thu: `docs/proof/phase-4/bench.json`, `docs/proof/phase-4/soak.json`  

---

## 1. Bảng ma trận nghiệm thu (Acceptance Criteria Trace Matrix)

| Mã AC | Nội dung yêu cầu | Cách kiểm chứng / Lệnh thực thi | Bằng chứng / File test | Kết quả |
| :---: | :--- | :--- | :--- | :---: |
| **AC-P4-01** | Test Contract v1.3: Khai báo `contract_version: "1.3"`, `bench_cmd` và `soak_cmd` ở gốc `game.contract.json` | Đọc `game.contract.json` & kiểm tra root schema | `tests/test_bench.py::test_bench_cmd_in_contract_and_cli`, `tests/test_soak.py::test_soak_cmd_trong_contract_ghi_dung_schema` | **ĐẠT** |
| **AC-P4-02** | Benchmark có render: `<bench_cmd> --seed 42 --duration 30 --out bench.json`<br>- Cảnh: Lặn sáng với độ tươi, cá bơi, Cá Sấu, Út Sen đứng yên ở bến.<br>- Làm nóng 3s, đo 30s tại 1280×720.<br>- Xuất 5 trường JSON, đạt avg ≥ 60 FPS, p1_low ≥ 30 FPS, load ≤ 10s | Chạy `python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json` | `docs/proof/phase-4/bench.json`<br>- avg_fps: **63.73** (≥ 60)<br>- p1_low_fps: **60.64** (≥ 30)<br>- frames: 1912<br>- measured_s: 30.004<br>- load_ms: 1 ms (≤ 10000) | **ĐẠT** |
| **AC-P4-03** | Cảnh báo dễ nhận biết & Chế độ Tương phản cao:<br>- 3 cảnh báo trực quan bằng chữ và biểu tượng:<br>  1. Thủy quái Cá Sấu ở gần: `🐊 CẢNH BÁO...`<br>  2. Bình Oxy sắp hết (≤ 20%): `🫁 NGUY HIỂM...`<br>  3. Khách bàn ăn sắp giận bỏ về (≤ 25%): `😤 CẢNH BÁO...`<br>- Chế độ Tương phản cao (High Contrast Mode) toggle qua nút HUD hoặc phím tắt `C` | Mở giao diện `chonoi.live`, kiểm tra DOM overlay và CSS `body.high-contrast` | `chonoi/web/index.html` (DOM IDs: `#threat-banner`, `#oxy-warning-banner`, `#customer-warning-banner`, `#btn-high-contrast`) | **ĐẠT** |
| **AC-P4-04** | Mở rộng: Phụ đề SFX (Accessibility Closed Captions):<br>- Hiển thị phụ đề trực quan khi phát các hiệu ứng âm thanh (quăng lưới, hái hoa, nấu bếp, món chín, trả tiền & boa, v.v.)<br>- Chơi thử khi tắt âm lượng vẫn nhận biết đầy đủ sự kiện âm thanh | Thao tác tương tác trong game, quan sát popup phụ đề nổi `#sfx-captions-box` | `chonoi/web/index.html` (`SoundFX` class & `showSFXSubtitle(icon, text)`) | **ĐẠT** |
| **AC-P4-05** | Soak headless: `<soak_cmd> --seed 7 --days 10 --out soak.json`<br>- Chạy 10 Ngày trong một tiến trình headless bằng bot tất định (gather → quan → shop).<br>- Kế hoạch D1–D5 lặp ở Ngày 6–10.<br>- Đạt: days_completed = days = 10, crashes = 0 | Chạy `python3 -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json` | `docs/proof/phase-4/soak.json`<br>- days: 10, days_completed: 10<br>- crashes: 0<br>- duration_s: ~14.309s | **ĐẠT** |
| **AC-P4-06** | Đóng gói & Phát hành v1.0.0 / v1.0.1 (kèm `LICENSE` MIT, `CREDITS.md`):<br>- Clone sạch chạy trong tối đa 3 lệnh trên macOS / Linux / Windows.<br>- Bộ test tự động 150/150 tests xanh 100%.<br>- Giữ vững tính tất định byte-for-byte và tính hồi quy các phase P1–P3 | Chạy smoke test, benchmark, soak và kiểm tra tài liệu phát hành | `tests/`, `README.md`, `CHANGELOG.md`, `game.contract.json` | **ĐẠT** |
| **AC-P4-07** | Gameplay, tuning, kho và JSONL theo v1.2 khi chạy contract `1.3` (độ tươi, kho cá thể, `spoiled`, file kho đếm → mã 2) | Chạy trên `game.contract.json` thật:<br>1. Smoke ngưỡng 30 TICKET-03: giỏ `{"id":"I1","kind":"ca_linh","fresh":30}`, 1 bước<br>2. Smoke bàn giao: gather cập bến → `quan --inventory --ticks 0`<br>3. `quan --inventory` với file `{"items":{"ca_loc":1}}` | 1. `spoiled` ở tick 1, `location: "hold"` (khớp ví dụ đề)<br>2. snapshot quán khớp **chính xác** id, kind, fresh của file<br>3. mã 2<br>`tests/test_smoke_p1.py::Integration`, `tests/test_quan_freshness.py`, `tests/test_gather_freshness.py`. Lỗi ở `v1.0.0` (thiếu `tuning.freshness`, schema chỉ bật khi version = "1.2") sửa ở commit `518f5fa` | **ĐẠT** (từ `v1.0.1`) |

---

## 2. Hướng dẫn chạy từ Clone sạch (Tối đa 3 lệnh)

### Trên Linux / macOS
```bash
git clone <repo_url> chonoi_app && cd chonoi_app
python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode day
```

### Trên Windows
```powershell
git clone <repo_url> chonoi_app; cd chonoi_app
py -3 -m unittest discover -s tests -v
py -3 -m chonoi.live --mode day
```

---

## 3. Bằng chứng kết quả Benchmark (`docs/proof/phase-4/bench.json`)

```json
{
  "avg_fps": 63.73,
  "p1_low_fps": 60.64,
  "frames": 1912,
  "measured_s": 30.004,
  "load_ms": 1
}
```
- **avg_fps = 63.73 FPS** $\ge 60$ FPS (ĐẠT)
- **p1_low_fps = 60.64 FPS** $\ge 30$ FPS (ĐẠT)
- **load_ms = 1 ms** $\le 10000$ ms (ĐẠT)

---

## 4. Bằng chứng kết quả Soak Test 10 Ngày (`docs/proof/phase-4/soak.json`)

```json
{
  "days": 10,
  "days_completed": 10,
  "crashes": 0,
  "results": [
    {
      "day": 1,
      "earned": 43,
      "reputation": 3.2,
      "score": 343
    },
    {
      "day": 2,
      "earned": 43,
      "reputation": 3.2,
      "score": 343
    },
    {
      "day": 3,
      "earned": 86,
      "reputation": 3.4,
      "score": 386
    },
    {
      "day": 4,
      "earned": 125,
      "reputation": 3.6,
      "score": 425
    },
    {
      "day": 5,
      "earned": 125,
      "reputation": 3.6,
      "score": 425
    },
    {
      "day": 6,
      "earned": 168,
      "reputation": 3.8,
      "score": 468
    },
    {
      "day": 7,
      "earned": 168,
      "reputation": 3.8,
      "score": 468
    },
    {
      "day": 8,
      "earned": 211,
      "reputation": 4.0,
      "score": 611
    },
    {
      "day": 9,
      "earned": 250,
      "reputation": 4.2,
      "score": 650
    },
    {
      "day": 10,
      "earned": 250,
      "reputation": 4.2,
      "score": 650
    }
  ],
  "duration_s": 14.309
}
```
- **days_completed = 10 / 10** (ĐẠT)
- **crashes = 0** (ĐẠT)
- Lặp kế hoạch ngày D1–D5 ở Ngày 6–10 chính xác theo yêu cầu.
- Từ `v1.0.1` giá món tính theo độ tươi (v1.2), nên `earned` thấp hơn bản `v1.0.0` (Ngày 1: 43 thay vì 48).

---

## 5. Kết quả kiểm thử hồi quy toàn diện (Regression Test Suite)

```text
Ran 150 tests in 15.462s
OK (100% test cases pass - contract 1.3 với tuning.freshness)
```
- Không có bất kỳ test case nào bị vỡ hoặc suy giảm hiệu năng.
- Tất cả các kiểm thử contract, rng, snapshot, và tích hợp liên phase đều đạt chuẩn.
