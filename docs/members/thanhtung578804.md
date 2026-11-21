# thanhtung578804 — Phản tư cá nhân (DEV 1: Lặn & Sinh Tồn)

## Phase 1
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

## Phase 2
- **Tôi đã làm (kèm link commit):**
  - Triển khai & tinh chỉnh hành vi sinh tồn nâng cao cho DEV 1: phối hợp logic Thủy quái Cá Sấu Năm Chèo (M1, M2), cơ chế cắn táp trừ 1 Máu và rơi $\lfloor\text{hold}/2\rfloor$ nguyên liệu theo cơ chế LIFO, bất tử 90 ticks và recoil 60 bước.
  - Tích hợp và bảo toàn tính năng sáng tạo áp suất sâu Mekong: bổ sung tiêu hao Oxy tăng gấp đôi (2 ticks/tick) tại vùng nước sâu $d > 18.0\text{m}$, kích hoạt `depth_warning` lên HUD overlay trên commit `ff4c58b`: [`chonoi/sim/gather.py`](../../chonoi/sim/gather.py).
  - Cập nhật test suite xác thực áp suất sâu [`tests/test_depth_pressure.py`](../../tests/test_depth_pressure.py) tương thích với kiến trúc Phase 2 (`Streams`, `IdAllocator`).
  - Tham gia nghiệm thu vòng lặp ngày (`--mode day`), shop nâng cấp và ma trận nghiệm thu [`docs/verification/phase-2.md`](../verification/phase-2.md).

- **Tôi đã review (kèm link):**
  - Review PR/commit tích hợp Phase 2 của DEV 2 (Phạm Quang Tuấn) và DEV 3/4 (Lê Ngọc Khánh, Chu Văn Nhật): kiểm tra kỹ các luồng chuyển tiếp `gather` sang `quan` và luồng mua nâng cấp ở Shop trong [`chonoi/sim/day.py`](../../chonoi/sim/day.py).

- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Khi hợp nhất code với `main`, AI ban đầu định viết lại độc lập một `DayRunner` riêng thay vì tận dụng cỗ máy trạng thái `DaySim` sẵn có của nhóm. Tôi đã kịp thời phát hiện qua `git log origin/main` để nhóm đồng nhất sử dụng `chonoi/sim/day.py`, tránh dư thừa mã nguồn.

- **Điều tôi học được:**
  - Kỹ năng tích hợp liên tục (CI) khi làm việc đồng thời 5 lập trình viên; biết cách quản lý state machine đa giai đoạn (DayIntro -> Gather -> EveningIntro -> Quan -> DayResult -> Shop) mà không phá vỡ tính tất định của engine headless.

## Phase 3
- **Tôi đã làm (kèm link commit):**
  - Hoàn thành toàn diện phân hệ Lặn độ tươi (`gather` freshness) theo Contract v1.2 — "Mùa Nước Nổi":
    * Chuyển đổi giỏ lặn `self.hold` sang kho cá thể `{id, kind, fresh}`.
    * Cấp ID duy nhất (`self.ids.new("I")`) và gán `fresh = 100.0` khi hái hoa (`_step_harvest`) và bắt cá (`_step_catch`).
    * Trừ hao độ tươi trong giỏ $0.5/\text{s}$ ($1/120$ mỗi tick), phát sự kiện `spoiled {item_id, kind, location: "hold"}` đúng thứ tự id khi đi từ $\ge 30$ xuống $< 30$.
    * Bàn giao mảng cá thể ở `gather_end.inventory` và hỗ trợ ghi file kho cá thể chuẩn byte-deterministic.
  - Xây dựng bộ test chuyên biệt 8 test case PASS 100%: [`tests/test_gather_freshness.py`](../../tests/test_gather_freshness.py) và lưu bằng chứng tại [`docs/proof/phase-3/gather-freshness-tests.md`](../proof/phase-3/gather-freshness-tests.md).

- **Tôi đã review (kèm link):**
  - Review phân hệ Quán độ tươi của DEV 3 (Lê Ngọc Khánh) trên PR #4 ([`chonoi/sim/freshness.py`](../../chonoi/sim/freshness.py), [`chonoi/sim/quan.py`](../../chonoi/sim/quan.py)), đảm bảo tính đồng bộ tuyệt đối về hằng số đơn vị phân số `Fraction` (UNITS = 240) giữa hai phân hệ Lặn và Quán.

- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI trong bước đầu tính hao tươi giỏ lặn dùng float trừ trực tiếp thay vì tận dụng hằng số `STEP_GATHER = Fraction(1, 120)` từ `freshness.py`, gây sai số dấu phẩy động nhỏ ở ngưỡng 30. Tôi đã bắt AI chuẩn hóa dùng `Fraction` và kiểm tra `assertAlmostEqual(places=9)`.

- **Điều tôi học được:**
  - Quản lý breaking change trong SDLC khi chuyển đổi schema dữ liệu từ đếm tổng (`dict`) sang cá thể hóa (`itemized list`), đồng thời giữ vững test contract backward compatibility.
