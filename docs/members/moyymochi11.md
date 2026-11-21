# moyymochi11 (Chu Văn Nhật - 2A202603848) — phản tư cá nhân (≤ 200 từ)

- Module phụ trách: DEV 5 — Gameplay Bếp Nấu, Bưng Bê & Kinh Tế Quán (`chonoi/sim/quan.py`)
- Tôi đã làm (kèm link commit):
  + Phase 1: Triển khai logic đun nấu bếp than, bốc món chín, phục vụ món tại bàn và thanh toán hóa đơn kèm tiền boa (tip), cộng điểm uy tín nhà hàng (`chonoi/sim/quan.py`).
  + Phase 2: Nâng cấp hỗ trợ 2 bếp than B1/B2 và 4 bàn T1-T4, đồng bộ doanh thu với chế độ Shop cuối ngày.
  + Phase 3: Triển khai và xác thực cơ chế Bếp nấu chốt giá theo độ tươi cá thể (Freshness Pricing: `base_price = floor(price * avg_fresh / 100)`) và tính tiền boa động dựa trên giá đã chốt (`tip = floor(base_price * 0.2)`).
  + Mở rộng bộ kiểm thử `tests/test_quan_kitchen_serving.py` bao phủ toàn diện các ca kiểm thử độ tươi v1.2 và ngăn chặn nấu nguyên liệu ươn (< 30).
- Tôi đã review (kèm link):
  + Review contract v1.2, cơ chế hao mòn tươi `freshness.py` và tích hợp giữa Bếp nấu với kho cá thể.
- AI sai ở đâu và tôi phát hiện thế nào:
  + AI ban đầu giả định nguyên liệu ươn bị xóa ngay lập tức khỏi snapshot `stock`, nhưng contract v1.2 quy định cá thể vẫn lưu trong kho cho đến khi dọn, chỉ là trạng thái khả dụng bị vô hiệu hóa (`available_stock = {}`). Tôi đã nhắc AI sửa lại assert kiểm tra đúng contract.
- Điều tôi học được:
  + Nắm vững quy trình làm việc nhóm theo mô hình feature branch trong Git, cách kiểm thử tính toán tài chính với số thập phân/phân số chính xác (Fraction) và phối hợp nhịp nhàng với AI Agent theo hợp đồng contract qua các phase.
