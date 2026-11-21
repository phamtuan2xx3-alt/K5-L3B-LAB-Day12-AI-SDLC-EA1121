# Quán Ăn Chợ Nổi — v1.0.1 (bản sửa của v1.0.0)

Bản này giữ toàn bộ nội dung của [v1.0.0](release-v1.0.0.md) và sửa một lỗi làm sai Test Contract v1.3.

## Sửa lỗi
- **Độ tươi và kho cá thể bị tắt khi chạy contract 1.3.** TICKET-04 giữ "gameplay, tuning, kho và JSONL theo v1.2",
  nhưng ở v1.0.0, `game.contract.json` thiếu `tuning.freshness` và bộ chọn schema chỉ bật kho cá thể khi version
  đúng bằng `"1.2"`. Hậu quả: giỏ, kho và file kho chạy theo kiểu đếm, smoke ngưỡng 30 của TICKET-03 trả mã 2.
  - Thêm `tuning.freshness {initial: 100, gather_decay_per_s: 0.5, quan_decay_per_s: 0.25, spoiled_below: 30}`.
  - Mọi contract từ 1.2 trở lên dùng kho cá thể `{id, kind, fresh}`.
  - Snapshot xuất `fresh` đủ chính xác để khớp đúng file kho khi bàn giao (tọa độ vẫn 3 chữ số).
- Thêm `LICENSE` (MIT) và hoàn thiện `CREDITS.md` (không dùng asset ngoài; danh sách công cụ AI).

## Đã kiểm trên contract thật
| Kiểm tra | Kết quả |
|---|---|
| `python3 -m unittest discover -s tests` | 150 test OK |
| Smoke ngưỡng 30 (TICKET-03): giỏ `{"id":"I1","kind":"ca_linh","fresh":30}`, 1 bước | `spoiled` ở tick 1, `location: "hold"` |
| Smoke bàn giao: gather cập bến → `quan --inventory --ticks 0` | snapshot quán khớp chính xác id, kind, fresh của file |
| File kho đếm `{"items":{"ca_loc":1}}` khi chạy contract 1.3 | mã 2 |
| `--mode day --days 1` | `reason: days_complete` |
| Chạy lặp cùng seed | JSONL giống từng byte |
| `python3 -m chonoi.soak --seed 7 --days 10` | 10/10 Ngày, 0 crash (`docs/proof/phase-4/soak.json`) |

Giá món giờ tính theo độ tươi, nên số tiền trong soak thấp hơn v1.0.0 một chút (Ngày 1: 43 thay vì 48). Đây là
hành vi đúng của v1.2.

## Cách chạy từ clone sạch (Linux / macOS, 3 lệnh)
```bash
git clone https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121.git chonoi && cd chonoi
python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather    # mở http://127.0.0.1:8000/
```
Windows: thay `python3` bằng `py -3`. Headless: `python3 -m chonoi.headless --mode gather|quan|day ...`.
Benchmark: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json`.

## Giới hạn đã biết
- Cần trình duyệt hiện đại hỗ trợ HTML5 Canvas và Web Audio API (Chrome, Edge, Firefox).
- Cần Python 3.10 trở lên cho headless và server live.
- Trên Windows, nếu test fail hàng loạt với mã 9009: `python3` trong PATH là lối tắt Microsoft Store, hãy bỏ
  `WindowsApps` khỏi PATH hoặc chạy bằng `py -3`.
