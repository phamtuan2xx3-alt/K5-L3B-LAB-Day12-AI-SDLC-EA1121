# BẢNG TỔNG HỢP 5 ĐẦU VIỆC GAMEPLAY (DEV 1 -> DEV 5)

> **Mô hình tổ chức:** 
> - **5 phần GAMEPLAY chuyên biệt:** Mỗi thành viên sở hữu 1 cơ chế gameplay độc lập trong game (Dave the Diver phong cách Miền Tây).
> - **FE / Đồ Họa Web (`client/ui`):** Là **CÔNG VIỆC CHUNG** của cả nhóm! Ai làm xong phần gameplay của mình thì cùng đóng góp giao diện/hiệu ứng cho tính năng đó (xem hướng dẫn tại [`shared-fe-visuals.md`](./shared-fe-visuals.md)).

---

## BẢNG PHÂN CHIA 5 ĐẦU VIỆC GAMEPLAY (MỞ CHO CẢ 5 DEV)

| STT | Tên Lát Gameplay | Module File | Thành viên nhận việc | GitHub Handle | Trạng thái | Hướng dẫn & Prompt AI |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **DEV 1** | **Gameplay Lặn & Sinh Tồn**<br>*(Bơi, Oxy, Ngạt nước, Mất máu, Ngất xỉu, Cập bến ghe)* | `chonoi/sim/gather.py` | *(Chưa nhận)* | `@...` | `Trống` | [`task-1-gather-survival.md`](./task-1-gather-survival.md) |
| **DEV 2** | **Gameplay Sinh Thái & Săn Bắt**<br>*(Hái Bông Súng/Điên Điển mọc lại, Săn Cá Linh/Cá Lóc, Giỏ LIFO)* | `chonoi/sim/gather.py` | Phạm Quang Tuấn (2A202603824) | `phamtuan2xx3-alt` | `In Progress` | [`task-2-gather-harvest.md`](./task-2-gather-harvest.md) |
| **DEV 3** | **Gameplay Thực Khách & Bàn Ăn**<br>*(Lịch đón khách ghé ghe, Xếp bàn ăn, Thanh kiên nhẫn, Khách giận bỏ về)* | `chonoi/sim/quan.py` | Lê Ngọc Khánh (2A202603804) | `lekhanh2k5-dotcom` | `In Progress` | [`task-3-quan-customers.md`](./task-3-quan-customers.md) |
| **DEV 4** | **Gameplay Kho Nguyên Liệu & Menu**<br>*(Kho khả dụng, Kiểm tra công thức nấu, Khóa giữ chỗ nguyên liệu, Xử lý hết món)* | `chonoi/sim/quan.py` | *(Chưa nhận)* | `@...` | `Trống` | [`task-4-quan-inventory-menu.md`](./task-4-quan-inventory-menu.md) |
| **DEV 5** | **Gameplay Bếp Nấu, Bưng Bê & Kinh Tế**<br>*(Nấu bếp than, Bưng bê món trên tay, Phục vụ khách ăn, Tiền, Tip & Uy tín)* | `chonoi/sim/quan.py` | Chu Văn Nhật (2A202603848) | `moyymochi11` | `In Progress` | [`task-5-quan-kitchen-serving.md`](./task-5-quan-kitchen-serving.md) |

---

## PHẦN VIỆC CHUNG (SHARED TASKS)
- **Giao diện Web & Đồ họa Canvas:** [`docs/plan/shared-fe-visuals.md`](./shared-fe-visuals.md) — Ai xong gameplay trước có thể vào vẽ thêm sprite, hiệu ứng nước, đèn lồng, khói bếp và âm thanh.
- **Quy trình Git:** Mỗi dev làm trên nhánh riêng `feat/<ten-module>`, commit tối thiểu 3 lần, chạy test xanh 100% trước khi tạo PR gộp vào `main`.
