# Changelog
## Unreleased

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
