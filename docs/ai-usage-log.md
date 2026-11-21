# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| P1 | lekhanh2k5-dotcom | Claude Code (Claude Opus) | Lát 3: viết `chonoi/sim/customers.py`, nối vào `quan.py`, 18 test trong `tests/test_quan_customers.py` | không đo | Test của starter lúc đầu fail hàng loạt (mã 9009) trên Windows vì `python3` trong PATH là lối tắt Microsoft Store, không phải lỗi code; bỏ lối tắt khỏi PATH thì 32/32 xanh. Người đọc lại thứ tự bước 4 → 5 với PRD F trước khi commit. |
| Phase 1 | Chu Văn Nhật | Claude / Gemini | Triển khai logic Bếp nấu & Kinh tế (`sim/quan`) và viết unit test | ~15k tokens | AI ban đầu định lưu trạng thái tạm vào customer làm lệch snapshot; nhắc AI chuyển sang stove để snapshot chuẩn contract. |
