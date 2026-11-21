# thanhtung578804 (Nguyễn Thanh Tùng - 2A202604084) — Phản tư cá nhân (≤ 200 từ)

- **Module phụ trách:** DEV 1 — Gameplay Lặn Sinh Tồn, Oxy & Độ Tươi (`chonoi/sim/gather.py`).
- **Tôi đã làm (kèm link commit):**
  - P1: Triển khai lặn/ngoi, tiêu hao/hồi phục oxy, đếm ngạt `choke`, trừ máu `hp`, ngất `fainted`, cập bến ghe `docked` và áp suất nước sâu: [ff4c58b](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/ff4c58b).
  - P2: Cơ chế Thủy quái Cá Sấu táp trừ máu và rơi $\lfloor\text{hold}/2\rfloor$ nguyên liệu LIFO: [649c25f](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/649c25f).
  - P3: Phân hệ Lặn độ tươi giỏ cá thể Contract v1.2, hao $0.5/\text{s}$, event `spoiled` và 8 unit test: [0d10c0e](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/commit/0d10c0e).
- **Tôi đã review & hỗ trợ:** Rà soát PR #4 của DEV 3 về độ tươi Quán, đảm bảo đồng nhất hằng số phân số `Fraction(1, 240)` giữa Lặn và Quán.
- **AI sai ở đâu và tôi phát hiện thế nào:** AI ban đầu trừ hao tươi bằng float trực tiếp gây sai số ở ngưỡng 30. Tôi phát hiện qua test fail và chuẩn hóa dùng `Fraction`.
- **Điều tôi học được:** Kỹ năng xử lý breaking change khi chuyển sang kho cá thể và duy trì tính tất định tuyệt đối.
