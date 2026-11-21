# Quán Ăn Chợ Nổi — Mekong River Simulation (Phase 4 / Release v1.0.0)

> Game mô phỏng 2D lấy cảm hứng phong cách lặn biển & kinh doanh nhà hàng phiên bản Miền Tây Sông Nước:
> - **Ban ngày (`gather`):** Út Sen lặn lòng sông Tiền Mekong, kiểm soát Oxy, hái Bông Điên Điển, Bông Súng, quăng lưới bắt cá theo cơ chế giỏ LIFO, né tránh Thủy Quái Năm Chèo và chụp ảnh Cá Hô Huyền Thoại.
> - **Ban đêm (`quan`):** Quán Ăn Chợ Nổi Má Tư lên đèn đón khách ghe cập mạn, kiểm tra kho nguyên liệu cá thể theo độ tươi, nấu 2 bếp than hồng, phục vụ thực khách trước khi hết kiên nhẫn, thu tiền và nhận tip.

---

## 1. Hướng Dẫn Chạy Nhanh Từ Clone Sạch (Tối Đa 3 Lệnh)

### Trên Linux / macOS
```bash
git clone https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121.git chonoi && cd chonoi
python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather
```

### Trên Windows (PowerShell)
```powershell
git clone https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121.git chonoi ; cd chonoi
py -3 -m unittest discover -s tests -v
py -3 -m chonoi.live --mode gather
```

Mở trình duyệt truy cập: `http://127.0.0.1:8000/`

---

## 2. Yêu Cầu Môi Trường & Điều Khiển

- **Môi trường:** Python 3.10 trở lên, không cần cài đặt thêm thư viện bên ngoài đối với game lõi và unit test.
- **Trình duyệt:** Google Chrome, Microsoft Edge, Mozilla Firefox (hỗ trợ HTML5 Canvas và Web Audio API).
- **Phím điều khiển:**
  - `W`, `A`, `S`, `D`: Di chuyển Út Sen (dưới sông / trong quán).
  - `E`: Tương tác (hái hoa, cập bến ghe, bốc món chín, phục vụ bàn ăn).
  - `SPACE`: Quăng lưới bắt cá dưới nước.
  - `Q`: Phóng lao xua quái vật.
  - `F`: Chụp ảnh Cá Hô Huyền Thoại.
  - `M` hoặc `H`: Bật/Tắt Bản đồ Thế giới mở 3/4 Isometric.
  - `C`: Bật/Tắt chế độ Tương Phản Cao (High Contrast Mode).
  - `P` / `Escape`: Tạm dừng game.
  - `R`: Khởi động lại lượt chơi.

---

## 3. Lệnh Kiểm Thử, Chạy Headless, Benchmark & Soak

- **Kiểm thử tự động (Unit Tests):**
  ```bash
  python3 -m unittest discover -s tests -v
  ```
  *(150/150 test cases đạt 100% PASS)*

- **Kiểm tra danh sách thành viên:**
  ```bash
  python3 tools/check_team.py
  ```

- **Chạy Headless (CLI xuất JSONL):**
  ```bash
  python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out gather.jsonl
  python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out quan.jsonl
  python3 -m chonoi.headless --mode day --seed 1 --days 5 --out day.jsonl
  ```

- **Đo hiệu năng Benchmark (`bench_cmd`):**
  ```bash
  python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json
  ```
  *(Kết quả: `avg_fps = 63.73`, `p1_low_fps = 60.64`, `load_ms = 1 ms`)*

- **Kiểm thử độ bền Soak Headless 10 Ngày (`soak_cmd`):**
  ```bash
  python3 -m chonoi.soak --seed 7 --days 10 --out docs/proof/phase-4/soak.json
  ```
  *(Kết quả: `days_completed = 10`, `crashes = 0`)*

---

## 4. Sáng Tạo Của Nhóm & Tính Tiếp Cận (Accessibility)

- **Chu kỳ 24 Giờ & Bản đồ 3/4 Isometric:** Dòng sông Tiền uốn lượn với nước phù sa, lục bình dập dềnh và 2 địa danh thực tế (Bến Lặn & Quán Ăn Má Tư).
- **Âm thanh & Phụ đề SFX (Accessibility):** Tổng hợp sóng âm sông nước, bọt khí, tiếng bếp xèo xèo qua Web Audio API; kèm phụ đề trực quan cho người khiếm thính hoặc khi tắt âm lượng.
- **Chế độ Tương Phản Cao:** Tối ưu hóa màu nền và đường viền độ tương phản cao cho người thị lực kém.
- **Bảo toàn Test Contract:** Toàn bộ tính năng sáng tạo được thiết kế decoupled, tự động tắt ở chế độ headless CLI để đảm bảo 100% tính tất định byte-for-byte.

---

## 5. Bản Đóng Gói Phát Hành & Video Demo

- **GitHub Release v1.0.0:** [https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/releases/tag/v1.0.0](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/releases/tag/v1.0.0)
- **Tải file Video Demo:** [demo_quan_an_cho_noi.mp4](https://github.com/phamtuan2xx3-alt/K5-L3B-LAB-Day12-AI-SDLC-EA1121/releases/download/v1.0.0/demo_quan_an_cho_noi.mp4)
- **Xem video tại máy cục bộ:** `demo_quan_an_cho_noi.mp4` trong thư mục gốc dự án.
