# moyymochi11 (Chu Văn Nhật - 2A202603848) — phản tư cá nhân (≤ 200 từ)

- **Vai trò:** DEV 5 — Bếp Nấu, Bưng Bê & Kinh Tế Quán (`chonoi/sim/quan.py`), Frontend & Release QA.
- **Phần tôi làm:**
  + P1–P3: Bếp than B1/B2, bàn T1–T4, chốt giá độ tươi v1.2, tiền boa động, test `test_quan_kitchen_serving.py`.
  + P4: Benchmark `chonoi/bench.py` (avg 63.73 FPS) tại `docs/proof/phase-4/bench.json`, test `test_bench.py`.
  + FE & UI: 3 cảnh báo trực quan (thủy quái 🐊, oxy 🫁, khách giận 😤), chế độ Tương Phản Cao (phím C / HUD) và Phụ đề âm thanh SFX Captions (`chonoi/web/index.html`).
- **Đã giúp ai:** Hỗ trợ DEV 3 kiểm chứng soak 10 ngày (`chonoi/soak.py`), phối hợp cập nhật contract v1.3.
- **AI sai ở đâu:** AI tạo `InputState` sai tham số trong `bench.py`; tôi sửa dùng `LiveInputs().advance()` chuẩn contract.
- **Bài học:** Kiểm thử hồi quy liên tục, thiết kế tiếp cận (accessibility) và tuân thủ contract giúp phát hành v1.0.0 thành công.
