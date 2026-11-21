# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Tích hợp 4 lát việc hoàn chỉnh và nhịp nhàng, 64/64 test cases xanh 100%. Giao diện Web Dave the Diver Mekong có cảnh báo quái viền tím và Shop trực quan.
- Điều tệ: Cần lưu ý các thay đổi giữa v1.0 và v1.1 (như điều kiện đủ chỗ cho cả đàn khi bắt cá) để cập nhật test regression kịp thời.
- 1 hành động cho Phase 3: Duy trì viết unit test cho từng cơ chế mở rộng (Lao xua, Rắn Hổ Mây, Cháy món) trước khi ráp nối.

## Phase 4 (cuối)
- Rà lại hành động Phase 2: Đã hoàn thành viết unit test cho các mở rộng, cập nhật độ tươi và bếp nấu test contract v1.2 & v1.3. Đảm bảo 100% test cases (150/150) xanh mướt.
- Điều tốt:
  + Tích hợp đầy đủ công cụ Benchmark (`chonoi/bench.py`) và Soak headless (`chonoi/soak.py`), cả hai tạo output json đúng chuẩn trong `docs/proof/phase-4/`.
  + Giao diện web được nâng cấp toàn diện: 3 cảnh báo trực quan với biểu tượng + chữ, chế độ Tương Phản Cao (High Contrast Mode) và Phụ đề âm thanh SFX Captions cho người khiếm thính/tắt âm lượng.
  + Nhóm phối hợp tốt, giữ vững tính tất định byte-for-byte và không phá vỡ bất kỳ test nào của các phase trước.
- Điều tệ:
  + Cần rà soát kỹ các tham số CLI của sub-commands trước khi chạy tự động để tránh mất thời gian xử lý argument parser error.
- Số liệu: 150/150 tests PASS, 10-day soak test hoàn thành không crash (crashes: 0, days_completed: 10), benchmark avg_fps 63.73, p1_low 60.64.
- Một lần AI sai và cách nhóm phát hiện:
  + AI khi viết `chonoi/bench.py` ban đầu truyền kwargs sai vào `InputState(move=[0,0], interact=False, catch=False)` gây TypeError. DEV 5 đã dùng `LiveInputs().advance()` để tạo input chuẩn theo contract và viết `tests/test_bench.py` kiểm tra schema benchmark.
- Nếu làm lại, đổi gì:
  + Thống nhất sớm định dạng payload của các công cụ benchmark và soak giữa các dev trước khi code để tích hợp mượt hơn.
