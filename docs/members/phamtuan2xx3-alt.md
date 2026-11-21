# phamtuan2xx3-alt (Phạm Quang Tuấn - 2A202603824) — Phản tư cá nhân (≤ 200 từ)

- **Module phụ trách:** DEV 2 — Sinh Thái & Săn Bắt Cá (`chonoi/sim/gather.py`).
- **Tôi đã làm (kèm link commit):**
  - Hái Bông Điên Điển, Bông Súng mặt nước và hồi 1200 ticks: [965d7ad](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/965d7ad).
  - Quăng lưới bắt Cá Linh, Cá Lóc, hồi chiêu 30 ticks, giỏ LIFO: [36b3d7a](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/36b3d7a).
  - Viết 12 test ca biên tại `tests/test_dev2_harvest_catch.py`: [3a43731](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/3a43731).
  - Tạo script tự động chơi & quay video demo `tools/record_demo.py`.
- **Tôi đã review & hỗ trợ:** Điều phối phản biện chuyên sâu qua Swarm Agents (Contract, Sim, Gameplay).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI dùng so sánh chuỗi `id` thường (`"F10" < "F2"`) vi phạm Contract E. Tôi phát hiện qua swarm critic và chuẩn hóa dùng `id_key`.
  - AI ban đầu bắn thừa `hold_full` khi bắt cá lúc giỏ còn chỗ; tôi đã chuẩn hóa chỉ bắn `fish_caught`.
- **Điều tôi học được:** Đảm bảo tính tất định byte-for-byte, khử nhiễu float jitter và quy trình AI SDLC kỷ luật.
