# lekhanh2k5-dotcom (Lê Ngọc Khánh - 2A202603804) — phản tư cá nhân (≤ 200 từ)

- Module phụ trách: DEV 3 — Gameplay Thực Khách & Bàn Ăn (`chonoi/sim/quan.py`, `chonoi/sim/customers.py`); P2 Quán v1.1; P3 Quán độ tươi.
- Tôi đã làm (kèm link commit):
  - P1 vòng đời khách [6b6b7b5](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/6b6b7b5), test [bdebe26](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/bdebe26).
  - Tích hợp quán DEV 3+4+5 ([PR #2](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/pull/2)), test tích hợp [5d68112](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/5d68112).
  - P2 lọc món theo kế hoạch Ngày [8054c60](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/8054c60).
  - P3 độ tươi, kho cá thể ([PR #4](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/pull/4): [36cb286](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/36cb286), [3a6dc30](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/3a6dc30)).
- Tôi đã review (kèm link): nhánh DEV 4, DEV 5 và commit [5c757d1](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/5c757d1) khi gộp vào PR #2. Ba bản lệch Test Contract E: món trên tay là tên món, `paid.total`, boa dùng `round` lúc trả tiền. Tôi sửa theo PRD và giữ nguyên tác giả các commit.
- AI sai ở đâu và tôi phát hiện thế nào: AI viết test sai luật (cho rằng bếp bận thì chuyển sang bếp kế, quên khách rời rồi khách mới vào cùng tick), và để độ tươi đọc lại từ file lệch một tick ở ngưỡng 30. Tôi phát hiện nhờ chạy test rồi đối chiếu từng câu PRD.
- Điều tôi học được: chốt hợp đồng (schema, tên event) trước khi code song song. Push thẳng `main` khiến nhóm có hai bản quán chạy song song.
