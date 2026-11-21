# moyymochi11 (Chu Văn Nhật - 2A202603848) — phản tư cá nhân (≤ 200 từ)

- Module phụ trách: DEV 5 — Gameplay Bếp Nấu, Bưng Bê & Kinh Tế Quán (`chonoi/sim/quan.py`)
- Tôi đã làm (kèm link commit):
  + Triển khai logic đun nấu bếp than, bốc món chín, phục vụ món tại bàn và thanh toán hóa đơn kèm tiền boa (tip), cộng điểm uy tín nhà hàng (`chonoi/sim/quan.py`).
  + Viết bộ kiểm thử unit tests `tests/test_quan_kitchen_serving.py` xác thực tính đúng đắn của chu trình dịch vụ ẩm thực miền Tây.
- Tôi đã review (kèm link):
  + Review contract `game.contract.json` và cấu trúc snapshot của `QuanSim`.
- AI sai ở đâu và tôi phát hiện thế nào:
  + AI ban đầu định lưu trạng thái khách nấu thẳng vào object khách gây phình to snapshot; tôi đã nhắc AI lưu liên kết vào stove và dùng `sort_by_id` để đảm bảo tính tất định deterministic.
- Điều tôi học được:
  + Nắm vững quy trình làm việc nhóm theo mô hình feature branch trong Git, cách viết test tự động và phối hợp nhịp nhàng với AI Agent theo hợp đồng contract.
