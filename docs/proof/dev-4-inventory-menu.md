# Phase 1 — Kiểm chứng phần kho và menu của DEV 4

- DEV 3: Sau khi tìm được bàn trống, gọi `_choose_dish_for_customer(events)`. Nếu trả về `(dish, reserved)`, lưu cả hai trường vào khách trước khi xét lượt khách tiếp theo. Nếu trả về `None`, sự kiện `no_dish` đã được thêm. Khi khách bỏ về, xóa phần giữ chỗ hoặc bỏ khách khỏi `self.customers`; kho thật chưa bị trừ cho phần nguyên liệu vẫn đang giữ chỗ.
- DEV 5: Gọi `_consume_reservation(customer)` trước khi chuyển bếp sang `cooking`. Hàm tự trừ kho và xóa giữ chỗ khi thành công. Nếu trả về `False`, giữ nguyên kho, phần giữ chỗ và trạng thái bếp.
- Hai điểm gọi trên chưa được nối vào `QuanSim.step()`. Quy tắc khi hết bàn đang chờ làm rõ trong [docs/clarify.md](../clarify.md).

```powershell
$env:PYTHONPATH = "tests;."
python -m unittest discover -s tests -v
```

Kết quả thực tế: 36/36 test đạt. Bốn test mới kiểm thứ tự chọn món, giữ và giải phóng nguyên liệu, cộng dồn giữ chỗ và báo hết món, trừ kho đúng một lần và giữ nguyên dữ liệu khi không đủ nguyên liệu. Bộ test hiện có cũng xác nhận quán đọc được kho do ca thu hoạch ghi.
