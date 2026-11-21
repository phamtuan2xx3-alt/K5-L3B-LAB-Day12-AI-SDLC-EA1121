# Changelog
## Unreleased

### Sửa sau v1.0.0 — bật độ tươi cho contract 1.3 (DEV 3)
- `game.contract.json` thêm `tuning.freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25,
  spoiled_below:30}`. `inventory.is_itemized`: mọi contract ≥ 1.2 dùng kho cá thể. Trước đây chỉ đúng `"1.2"`,
  nên với `"1.3"` độ tươi bị tắt và smoke ngưỡng 30 của TICKET-03 trả mã 2.
- JSONL: khóa `fresh` xuất đủ chính xác (tọa độ vẫn làm tròn 3 chữ số), để snapshot quán khớp chính xác file kho.
- Test: unit test luật kho đếm dùng `helpers.counts_tuning()` (manifest v1.0/1.1); smoke CLI trong
  `test_smoke_p1` đổi sang mảng cá thể. Luật kiểm không đổi. 150 test OK.

### Phase 4 — Phát hành v1.0.0 (DEV 5 & QA)
- `contract_version` = `"1.3"`, khai báo `bench_cmd` và `soak_cmd` ở gốc `game.contract.json`.
- `bench_cmd` = `python3 -m chonoi.bench --seed <int> --duration <giây> --out bench.json`:
  Đo hiệu năng cảnh lặn ban ngày seed 42 tại 1280x720, làm nóng 3s, đo 30s. Kết quả: avg 63.73 FPS (>= 60),
  1% low 60.64 FPS (>= 30), load 1ms (<= 10s) tại `docs/proof/phase-4/bench.json`.
- Ba cảnh báo trực quan dễ nhận biết: Thủy quái Cá Sấu ở gần (🐊), Bình oxy sắp hết (🫁 <= 20%), Khách bàn ăn sắp giận bỏ về (😤 <= 25%).
- Chế độ Tương Phản Cao (High Contrast Mode) toggle qua nút HUD hoặc phím tắt `C`.
- Phụ đề âm thanh SFX Captions hiển thị trực quan các sự kiện âm thanh phục vụ tính tiếp cận (Accessibility).
- Bộ test hồi quy `tests/test_bench.py` và duy trì 146/146 unit test xanh 100%.

### Phase 4 — soak headless (DEV 3)
- `soak_cmd` = `python3 -m chonoi.soak --seed <int> --days <N> --out soak.json` (khai ở gốc `game.contract.json`).
  Chạy N Ngày trong một tiến trình bằng bot tất định (gather → quan → shop), xuất `days, days_completed,
  crashes, results[{day, earned, reputation, score}], duration_s`. Seed 7, 10 Ngày: 10/10, 0 crash, ~2.5 s
  (`docs/proof/phase-4/soak.json`).
- `DaySim._get_plan`: Ngày 6–10 lặp kế hoạch D1–D5 (trước đây Ngày > 5 luôn dùng D1).

### Contract v1.2 — "Mùa Nước Nổi" (Phase 3) · BREAKING
- **Kho đếm → kho cá thể.** File kho, `gather.hold`, `quan.stock`, snapshot `stock`/`hold` đổi từ object
  `{"kind": số}` sang mảng `[{"id","kind","fresh"}]`. Kho rỗng là `{"items":[]}`. Khi chạy contract 1.2,
  file kho đếm, kind lạ, id trùng hoặc `fresh` ngoài [0, 100] trả **mã 2**.
- **Giữ chỗ theo id.** `customers[].reserved` đổi từ map `{"kind": số}` sang mảng id cá thể.
- **Giá theo độ tươi.** `base_price = floor(giá niêm yết × trung bình fresh / 100)`, chốt lúc bắt đầu nấu.
  Boa tính trên giá đã chốt. `cook_started.items` là mảng cá thể, sắp theo kind rồi id.
- **Event mới** `spoiled {item_id, kind, location}` khi cá thể đi từ ≥ 30 xuống < 30.
- Cách bật: thêm `tuning.freshness {initial:100, gather_decay_per_s:0.5, quan_decay_per_s:0.25,
  spoiled_below:30}` và `contract_version:"1.2"`. Chưa có `freshness` thì code chạy schema v1.1 như cũ.

**Cập nhật fixture:** `{"stock":{"ca_loc":1}}` → `{"stock":[{"id":"I1","kind":"ca_loc","fresh":100}]}`;
`"reserved":{"ca_loc":1}` → `"reserved":["I1"]` (hoặc bỏ để hệ thống tự cấp cá thể tươi nhất).

Đã làm:
- Phía Quán + đọc/ghi file kho cá thể (DEV 3, PR #4).
- Phía Lặn: giỏ cá thể, hao 0.5/s, `spoiled` location `hold`, `gather_end.inventory` mảng cá thể (DEV 1, thanhtung578804).
Còn lại: bàn giao trong `day`, HUD độ tươi, và đổi `game.contract.json` sang 1.2.
