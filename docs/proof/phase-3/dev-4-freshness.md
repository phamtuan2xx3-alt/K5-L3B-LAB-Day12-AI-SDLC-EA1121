# DEV 4 — Bằng chứng tích hợp Phase 2 và Phase 3

- Runner `day` dùng kế hoạch trong manifest. Nếu scenario ghi đè một Ngày, hệ thống tính lại nguyên liệu từ công thức và số suất, rồi từ chối giá trị `ingredients` khai sai.
- CLI chọn schema kho theo phiên bản manifest. File kho 1.2 giữ đúng nhánh ở ngưỡng 30 ngay cả với giá trị sát dưới 30. Giá trị biểu diễn của một bội 1/240 vẫn đọc lại đúng bội đã ghi.
- Phần kho cá thể và giữ chỗ của DEV 3 được dùng chung khi tích hợp. Manifest vẫn ở 1.1, nên cần chạy lại smoke bàn giao toàn vòng `day` khi nhóm bật 1.2.

```powershell
$env:PYTHONPATH = "tests;."
python -m unittest discover -s tests -q
```

Kết quả: **129/129 test đạt**, gồm hồi quy Phase 1–2, kiểm thử kho cá thể và kiểm thử mới cho kế hoạch ghi đè, chọn schema theo phiên bản, nguyên liệu sai kiểu và độ tươi sát dưới 30.
