# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | P1 | Khách chưa được phục vụ thì `base_price`, `tip` trong snapshot là gì? PRD chỉ nói giá chốt lúc bắt đầu nấu, boa chốt lúc phục vụ. | Giả định: `null` tới khi được chốt. `eat_ticks_left = 0` khi chưa ăn (PRD D: "bộ đếm chưa kích hoạt mặc định 0"). | DEV 3 (lekhanh2k5-dotcom), chờ Anh Năm xác nhận |
| 2 | P1 | Chỉ có 1 món nấu được thì có rút RNG không? | Luôn rút `Streams("customer_dish").choice` trên danh sách món nấu được sắp theo mã Unicode, kể cả khi chỉ còn 1 món. Cách này nhất quán trong bản nộp (PRD E). | DEV 3 |
| 3 | P1 | Lượt khách rơi đúng tick khách cũ vừa hết kiên nhẫn? | Bước 4 cho khách cũ rời, nhả giữ chỗ trước, rồi bước 5 mới xét lượt mới, nên khách mới vào được ngay tick đó (ví dụ tick 3720 = 120 + 4×900). | DEV 3, theo thứ tự mục F |
| 4 | P1 | Kiểm mâu thuẫn fixture khách nào thì trả mã 2? | Trường lạ, `dish_id` ngoài menu, `state`/`order_status` sai, bộ đếm âm hoặc vượt trần (kiên nhẫn > `patience_s`, ăn > `eat_s`), `eating` mà không `served` hoặc thiếu giá/boa, đơn không phải `reserved` mà còn giữ chỗ, giữ khác công thức, tổng giữ vượt tồn, đơn `assigned` không có đúng 1 món ở bếp/tay, món ở bếp/tay trỏ sai đơn. | DEV 3 |
