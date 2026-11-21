# Quán Ăn Chợ Nổi — Bản Phát Hành Chính Thức v1.0.0 (Phase 4)

## 🌟 Điểm Mới (What's New)
- **Vòng lặp Gameplay Hoàn chỉnh (Dave the Diver phong cách Miền Tây Sông Nước):**
  - **Ban ngày (`gather`):** Út Sen lặn sông Mekong, kiểm soát bình Oxy, độ sâu nước, tránh ngạt và mất máu, hái Bông Điên Điển/Bông Súng/Kèo Nèo, săn Cá Linh/Cá Lóc/Cá Kèo bằng lưới LIFO, né tránh hoặc dùng Lao xua (`Q`) đẩy lùi Thủy Quái Cá Sấu Năm Chèo, chụp ảnh Cá Hô Huyền Thoại (`F`) để tăng uy tín nhà hàng.
  - **Ban đêm (`quan`):** Quán Ăn Chợ Nổi Má Tư lên đèn đón khách ghe cập mạn, kiểm tra tồn kho nguyên liệu, phục vụ thực khách 6 món ăn đặc sản miền Tây qua 2 bếp than hồng và 4 bàn ăn, nhận tiền, nhận tip và tích lũy uy tín.
- **Chu kỳ 24 Giờ & Bản đồ Thế giới mở:**
  - Chu kỳ Master Clock 24H in-game = 8 phút ngoài đời thực (1s thực = 3 phút in-game).
  - Bản đồ 3/4 Isometric uốn lượn dòng sông Tiền Mekong, hiển thị trực quan 2 màn chơi thực tế theo kế hoạch 5 Dev: Bến Lặn Sông Tiền và Quán Ăn Chợ Nổi Má Tư.
- **Hiệu năng & Khả năng tiếp cận (Accessibility):**
  - **Benchmark:** Đạt trung bình **63.73 FPS** (chuẩn $\ge 60$ FPS) và 1% low **60.64 FPS** (chuẩn $\ge 30$ FPS), thời gian load 1 ms ($\le 10$s).
  - **Soak Test Headless:** Hoàn thành 10 Ngày liên tục không crash (`days_completed: 10`, `crashes: 0`).
  - **3 Cảnh báo trực quan:** Biểu tượng chữ và icon cho Thủy quái đến gần (`🐊`), Bình oxy cạn (`🫁`), và Khách sắp giận bỏ về (`😤`).
  - **Chế độ Tương Phản Cao (High Contrast Mode):** Chuyển đổi nhanh qua phím tắt `C` hoặc nút HUD.
  - **Phụ đề Âm thanh SFX Captions:** Hỗ trợ người khiếm thính hoặc khi tắt âm lượng.

## 🚀 Hướng Dẫn Chạy Nhanh Từ Clone Sạch (Tối đa 3 Lệnh)

### Windows
```powershell
git clone https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121.git chonoi ; cd chonoi
py -3 -m unittest discover -s tests -v
py -3 -m chonoi.live --mode gather
```

### Linux / macOS
```bash
git clone https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121.git chonoi && cd chonoi
python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather
```

Truy cập giao diện tại: `http://127.0.0.1:8000/`

## 🧪 Kết Quả Kiểm Thử
- **Unit Test:** `Ran 150 tests in 21.182s — OK` (150/150 test cases đạt 100% Pass).
- **Soak Headless:** `python3 -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json` đạt 10/10 Ngày, 0 crash.
- **Benchmark:** `python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json` đạt 63.73 FPS.

## ⚠️ Giới Hạn Đã Biết (Known Limitations)
- Khuyến nghị sử dụng trình duyệt hiện đại (Google Chrome, Microsoft Edge, Mozilla Firefox) hỗ trợ HTML5 Canvas và Web Audio API.
- Cần Python 3.10 trở lên để chạy chế độ headless và server live.
