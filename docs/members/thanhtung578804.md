# thanhtung578804 — Phản tư cá nhân (DEV 1: Lặn & Sinh Tồn)

- **Tôi đã làm (kèm link commit):**
  - Triển khai toàn bộ cơ chế lõi của ca lặn `gather` cho Út Sen: chuyển vùng lặn/ngoi (`dive`/`surface`), tiêu hao & hồi phục oxy, đếm nhịp ngạt nước (`choke`), trừ máu (`hp`), ngất xỉu mất giỏ đồ (`fainted`) và cập bến ghe (`docked`).
  - Phát triển tính năng sáng tạo "Áp suất dòng sâu Mekong" (`depth_warning`) khi lặn sâu $d > 18.0$ và cảnh báo trực quan trên HUD web: [`chonoi/sim/gather.py`](../../chonoi/sim/gather.py), [`tests/test_depth_pressure.py`](../../tests/test_depth_pressure.py).
  - Viết bộ unit test chuyên biệt đảm bảo 100% độ bao phủ cho tính năng sinh tồn và tính năng sáng tạo: [`tests/test_depth_pressure.py`](../../tests/test_depth_pressure.py).

- **Tôi đã review (kèm link):**
  - Review phân công các bạn DEV 2, 3, 5 trong [`TEAM.md`](../../TEAM.md) và [`docs/plan/tasks-summary.md`](../plan/tasks-summary.md), đảm bảo không xảy ra xung đột trường dữ liệu giữa các lát cắt gameplay.

- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu kiểm tra độ sâu ngặt nghèo `> 18.0` khiến test bị lệch biên dấu phẩy động tại đúng điểm chuyển tiếp (`18.0` so với `18.000000000000004`). Tôi đã phát hiện qua assert fail của `unittest` và yêu cầu chuẩn hóa bằng `assertGreaterEqual` và làm tròn 3 chữ số theo đúng chuẩn Test Contract.

- **Điều tôi học được:**
  - Nắm vững kiến trúc vòng lặp game tick-based (60 Hz), tính tất định (determinism) qua RNG Streams và kỹ năng chia nhỏ các lát cắt tính năng (vertical slice) để tránh xung đột khi làm việc nhóm song song.
