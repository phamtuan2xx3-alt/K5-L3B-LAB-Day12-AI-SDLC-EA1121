# QuangAnh28 (Nguyễn Quốc Quang Anh - 2A202604120) — Phản tư cá nhân (≤ 200 từ)

- **Module phụ trách:** DEV 4 — Kho nguyên liệu & Menu (`chonoi/inventory.py`, `chonoi/sim/quan.py`).
- **Tôi đã làm:**
  - P1 — Tính kho khả dụng, chọn món, giữ chỗ và trừ kho khi nấu. [348f917](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/348f917)
  - P2 — Dùng kế hoạch ngày từ cấu hình và kiểm tổng nguyên liệu theo số suất. [13fd59e](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/13fd59e)
  - P3 — Chọn schema kho theo phiên bản và sửa lỗi đọc độ tươi sát ngưỡng 30. [eb8daa2](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/eb8daa2)
- **Tôi đã đối chiếu và hỗ trợ:** Rà luồng khách của DEV 3 và luồng bếp của DEV 5, ghi cách nối giữ chỗ và trừ kho đúng một lần. [Ghi chú bàn giao](../proof/dev-4-inventory-menu.md)
- **AI sai ở đâu và tôi phát hiện thế nào:** Lượt kiểm đầu bỏ sót ca sát dưới 30. Fixture `29.999999999` cho thấy phép làm tròn có thể biến hàng ươn thành hàng còn tươi. Tôi sửa bộ đọc và thêm test hồi quy. [Bằng chứng](../proof/phase-3/dev-4-freshness.md)
- **Điều tôi học được:** Kiểm thử cả hai phía của ngưỡng và đọc lại file kho để xác nhận dữ liệu bàn giao vẫn đúng.
