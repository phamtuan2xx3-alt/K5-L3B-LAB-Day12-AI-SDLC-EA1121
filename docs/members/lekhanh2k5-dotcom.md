# lekhanh2k5-dotcom (Lê Ngọc Khánh - 2A202603804) — phản tư cá nhân (≤ 200 từ)

- Module phụ trách: DEV 3 — Thực Khách & Bàn Ăn (`sim/customers.py`, `sim/quan.py`); P2 Quán v1.1; P3 Quán độ tươi.
- Tôi đã làm (kèm link commit):
  - P1 vòng đời khách [6b6b7b5](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/6b6b7b5)
  - Tích hợp quán ba lát [PR #2](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/pull/2)
  - P2 lọc món theo kế hoạch Ngày [8054c60](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/8054c60)
  - P3 độ tươi, kho cá thể [PR #4](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/pull/4)
- Tôi đã review (kèm link): nhánh DEV 4, DEV 5 và [5c757d1](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/5c757d1) khi gộp vào PR #2. Các bản này lệch Test Contract (món trên tay là tên món, `paid.total`, boa `round`). Tôi sửa theo PRD, giữ tác giả commit.
- AI sai ở đâu và tôi phát hiện thế nào: AI viết test sai luật (bếp bận thì chuyển bếp kế; quên khách rời rồi khách mới vào cùng tick) và đọc độ tươi từ file lệch một tick ở ngưỡng 30. Tôi phát hiện nhờ chạy test, đối chiếu PRD.
- Điều tôi học được: chốt hợp đồng trước khi code song song; push thẳng `main` dễ sinh hai bản trùng.
