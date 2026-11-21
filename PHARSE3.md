# TICKET-03 — Thế Giới Mở Chợ Nổi & Chu Trình 24H (Phase 3)

> **Mô hình gameplay:** Chu kỳ 24 giờ hoàn chỉnh kiểu *Dave the Diver: Mekong River Edition*.  
> **Vòng lặp cốt lõi:** Lặn bắt xong (06:00 - 15:00) $\to$ Chuẩn bị đồ & Chợ Chú Sáu (15:00 - 18:00) $\to$ Mở Quán Ăn Má Tư (18:00 - 23:00) $\to$ Về Ghe Nghỉ Ngơi (23:00 - 06:00) $\to$ Sang ngày mới.

---

## 1. QUY ĐỔI THỜI GIAN IN-GAME & ĐỜI THỰC (TIME SCALE)

- **Chu kỳ 1 Ngày (24 giờ in-game = 1.440 phút game):** Tương đương **8 phút ngoài đời thực** (480 giây = 28.800 ticks @ 60 Hz).
- **Tỷ lệ quy đổi chuẩn:**
  - $1\text{ phút ngoài đời} = 3\text{ giờ trong game}$ ($180\text{ phút in-game}$).
  - $1\text{ giây ngoài đời} = 3\text{ phút trong game}$ ($180\text{ giây in-game}$).
  - $1\text{ tick (1/60s)} = 3\text{ giây trong game}$.

### Phân Bổ 4 Khung Giờ Trong Ngày:

| Khung Giờ In-Game | Giai Đoạn (Phase) | Thời Lượng Đời Thực | Địa Điểm Mở Cửa | Hoạt Động Của Út Sen |
| :---: | :---: | :---: | :---: | :--- |
| **06:00 – 15:00**<br>(9 giờ in-game) | **Ca Lặn Sông Mekong**<br>(`gather`) | 180 giây<br>(3 phút, 10.800 ticks) | **Bến Lặn Sông Tiền** *(Mở)*<br>Quán ăn *(Đóng)* | Bơi lặn sông sâu, quản lý Oxy/Máu, hái hoa mặt nước, bắt cá Linh/Lóc/Kèo, né tránh Cá Sấu Năm Chèo & Rắn Hổ Mây. Cập bến ghe trước 15:00. |
| **15:00 – 18:00**<br>(3 giờ in-game) | **Chuẩn Bị & Chợ Nổi**<br>(`prep` / `hub`) | 60 giây<br>(1 phút, 3.600 ticks) | **Chợ Nổi Chú Sáu** *(Mở)*<br>Bến Lặn *(Đóng)* | Chèo xuồng ghé Chợ Chú Sáu: bán cá/hoa dôi dư lấy tiền, mua thêm nguyên liệu thiếu, mua nâng cấp bình Oxy/Áo phao/Lao xua, kiểm tra menu Má Tư. |
| **18:00 – 23:00**<br>(5 giờ in-game) | **Mở Quán Ăn Chợ Nổi**<br>(`quan`) | 180 giây<br>(3 phút, 10.800 ticks) | **Quán Ăn Má Tư** *(Mở)*<br>Bến Lặn *(Đóng)* | Quán lên đèn lồng đón khách ghe: nấu 2 bếp lò than, bưng bê phục vụ 4 bàn, giữ chỗ nguyên liệu, thu tiền, nhận tiền tip & tích lũy uy tín. |
| **23:00 – 06:00**<br>(7 giờ in-game) | **Tổng Kết & Đi Ngủ**<br>(`sleep` / `summary`) | 60 giây<br>(1 phút, 3.600 ticks) | **Ghe Nghỉ Út Sen** *(Mở)*<br>Quán ăn & Bến *(Đóng)* | Dọn dẹp đóng quán, kết toán doanh thu trong ngày, trở về Ghe Nghỉ Út Sen ngủ để hồi phục 100% Oxy/Máu và chuyển sang Ngày tiếp theo (D1 $\to$ D5). |

---

## 2. LOGIC HUB BẢN ĐỒ THẾ GIỚI MỞ (OVERWORLD NAVIGATION)

### 2.1. Bản Đồ Hub & Cơ Chế Mở/Đóng Theo Khung Giờ

Nhân vật Út Sen chèo xuồng trên bản đồ sông nước Chợ Nổi để di chuyển giữa 4 khu vực. Hệ thống tự động kiểm tra thời gian in-game để cho phép truy cập:

```text
               ┌──────────────────────────────────────────────┐
               │         BẢN ĐỒ KHU VỰC CHỢ NỔI MEKONG        │
               │           [Thời gian: 16:30 CHIỀU]           │
               └──────────────────────┬───────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
   [1. BẾN LẶN SÔNG TIỀN]    [2. CHỢ NỔI CHÚ SÁU]      [3. QUÁN ĂN MÁ TƯ]
      (06:00 - 15:00)           (15:00 - 22:00)           (18:00 - 23:00)
    ⛔ ĐÓNG: Nước chảy xiết    🟢 ĐANG MỞ: Mua bán đồ    ⏳ CHỜ: Mở lúc 18:00
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                            [4. GHE NGHỈ ÚT SEN]
                               (22:00 - 06:00)
                             💤 MỞ KHI KẾT CA ĐÊM
```

- **Quy tắc chuyển cảnh tự động:**
  1. Hết ca lặn (cập bến ghe hoặc 15:00) $\to$ Chuyển sang màn hình Hub / Chợ Nổi Chú Sáu để chuẩn bị đồ.
  2. Xong bước chuẩn bị (hoặc bấm `Sẵn sàng mở quán` / 18:00) $\to$ Vào Quán Ăn Chợ Nổi phục vụ khách.
  3. Hết ca quán (23:00) $\to$ Hiện bảng kết toán doanh thu $\to$ Di chuyển về Ghe Nghỉ Út Sen bấm `Ngủ` $\to$ Bình minh 06:00 hôm sau.

---

## 3. CƠ CHẾ NÂNG CẤP & MỞ RỘNG (PHASE 3 EXTENSIONS)

### 3.1. Lao Xua Quái Vật (`weapon`)
- Phím tắt: `Q` (nút `attack`).
- Mở khóa: Mua tại Shop / Chợ Chú Sáu.
  - Cấp 1 (300k): Bán kính quét 4.0 m, gây choáng quái vật 2.0 s (120 ticks), đẩy lùi 3 m ra xa.
  - Cấp 2 (600k): Bán kính quét 6.0 m, gây choáng 3.0 s (180 ticks), đẩy lùi 3 m.
- Thời gian hồi: 3.0 s (180 ticks) từ lúc bấm.
- Tác dụng: Choáng Cá Sấu Năm Chèo (M1, M2) hoặc Rắn Hổ Mây (M3), chặn cú táp của quái vật.

### 3.2. Chợ Chú Sáu (`vendor`)
- Cho phép mua bán trực tiếp trong giai đoạn chuẩn bị đồ (`prep`):
  - Giá bán cho Chú Sáu: Cá lóc 20k, Cá linh 8k, Cá kèo 10k, Bông hoa 5k.
  - Giá mua từ Chú Sáu: Bằng $\lfloor \text{Giá bán} \times 1.5 \rfloor$ (Cá lóc 30k, Cá linh 12k, Cá kèo 15k, Bông hoa 7k).
  - Giúp giải quyết tình trạng thiếu nguyên liệu nấu món trong thực đơn tối.

### 3.3. Sổ Tay Sinh Vật & Cá Hô Huyền Thoại (`ca_ho`)
- Cá Hô (H1): Bơi ở vùng nước sâu $d \in [10, 30]$, kích thước khổng lồ, bơi chậm 1.0 m/s.
- Không thể bắt thông thường (bắt sẽ phát event `released`).
- Phím `F` (`photo`): Chụp ảnh Cá Hô trong bán kính $\le 6.0$ m $\to$ Thưởng $+0.5$ Uy tín quán ăn (tối đa 1 lần/ngày).
