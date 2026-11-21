# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 21/11 10:15 | Khi giỏ gần đầy (11/12) mà bắt Cá Linh (yield 3), xử lý thế nào ở Phase 2? | Contract v1.1 quy định cần đủ chỗ cho cả đàn (`space >= y`), nếu thiếu chỗ thì phát `hold_full` và giữ đàn cá trong sông. | Giảng viên / PHARSE2.md |
| 2 | 21/11 10:20 | Rơi nguyên liệu khi bị Cá Sấu Năm Chèo táp? | Mất 1 Máu và bỏ `floor(hold / 2)` nguyên liệu theo chuẩn LIFO (nhặt sau mất trước). | PO / TICKET-02 |
| 3 | 21/11 10:30 | Hiệu lực của nâng cấp Shop mua cuối ngày? | Trừ tiền ngay, hiển thị cấp mới trong snapshot nhưng chỉ có hiệu lực thực tế (oxy, máu) từ Ngày kế tiếp. | Integrator / PHARSE2.md |
