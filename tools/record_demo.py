"""Tự động chơi và quay video demo hoàn chỉnh cho Quán Ăn Chợ Nổi (Phase 4).
Yêu cầu: Playwright, Chromium, ffmpeg.
Output: demo_quan_an_cho_noi.mp4 (< 5 phút, 1280x720 chuẩn bài nộp).
"""

import os
import time
import subprocess
import shutil
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "demo_recordings"
FINAL_VIDEO = "demo_quan_an_cho_noi.mp4"

def record():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("🚀 Bắt đầu khởi chạy Playwright Chromium để quay video...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 720}
        )
        page = context.new_page()

        print("🌐 Đang truy cập http://127.0.0.1:8000/ ...")
        page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
        page.wait_for_selector("#hud", timeout=10000)
        time.sleep(2.0)

        # ---------------------------------------------------------------------
        # PHẦN 1: BẬT / TẮT CHẾ ĐỘ TƯƠNG PHẢN CAO & SFX ĐỂ DEMO ACCESSIBILITY
        # ---------------------------------------------------------------------
        print("👁️ Demo chế độ Tương phản cao (High Contrast Mode)...")
        page.keyboard.press("c")
        time.sleep(1.5)
        page.keyboard.press("c")
        time.sleep(1.0)

        # ---------------------------------------------------------------------
        # PHẦN 2: LẶN SÔNG MEKONG (GATHER) — BƠI, HÁI HOA, BẮT CÁ, LAO XUA, CẬP BẾN
        # ---------------------------------------------------------------------
        print("🌊 Đang tự động chơi ca lặn ban ngày (gather)...")
        # Bơi sang phải (D) hướng về phía bãi hoa và đàn cá
        page.keyboard.down("d")
        time.sleep(3.5)
        page.keyboard.up("d")

        # Hái hoa điên điển / bông súng
        print("🌸 Hái hoa bông súng / điên điển (E)...")
        page.keyboard.press("e")
        time.sleep(0.8)

        # Bơi tiếp và lặn xuống (S + D)
        page.keyboard.down("s")
        page.keyboard.down("d")
        time.sleep(2.5)
        page.keyboard.up("s")
        page.keyboard.up("d")

        # Bắt cá dưới nước (Space)
        print("🐟 Quăng lưới bắt cá (Space)...")
        page.keyboard.press("Space")
        time.sleep(1.0)
        page.keyboard.press("Space")
        time.sleep(1.0)

        # Biểu diễn Lao xua quái vật (Q)
        print("🛡️ Dùng Lao xua quái vật (Q)...")
        page.keyboard.press("q")
        time.sleep(1.2)

        # Chụp ảnh Cá Hô Huyền Thoại (F)
        print("📸 Chụp ảnh Cá Hô Huyền Thoại (F)...")
        page.keyboard.press("f")
        time.sleep(1.5)

        # Bơi sâu hơn để minh họa áp suất và cảnh báo
        page.keyboard.down("s")
        time.sleep(2.0)
        page.keyboard.up("s")

        # Nổi lên mặt nước (W) và bơi về bến (A)
        print("⚓ Bơi trở về bến ghe Út Sen (W + A)...")
        page.keyboard.down("w")
        page.keyboard.down("a")
        time.sleep(3.0)
        page.keyboard.up("w")

        # Tiếp tục bơi sang trái về sát bến ghe X=2
        page.keyboard.down("a")
        time.sleep(4.0)
        page.keyboard.up("a")

        # Bấm Cập bến (E)
        print("⚓ Cập bến ghe Út Sen (E)...")
        page.keyboard.press("e")
        time.sleep(2.5)

        # ---------------------------------------------------------------------
        # PHẦN 3: BẢN ĐỒ THẾ GIỚI MỞ 3/4 ISOMETRIC
        # ---------------------------------------------------------------------
        print("🗺️ Mở Bản đồ Thế giới mở Chợ Nổi Mekong 3/4...")
        # Bấm nút về bản đồ chính
        btn_map = page.query_selector("#btn-return-map")
        if btn_map and btn_map.is_visible():
            btn_map.click()
            time.sleep(2.5)
        else:
            page.keyboard.press("m")
            time.sleep(2.5)

        # Xem bản đồ 3/4 và bấm chuyển sang Quán Ăn Chợ Nổi Má Tư
        print("🍜 Chọn Quán Ăn Chợ Nổi Má Tư...")
        page.evaluate("selectZoneOn3DMap('quan_an')")
        time.sleep(2.0)

        btn_enter = page.query_selector("#btn-popup-enter")
        if btn_enter and btn_enter.is_visible():
            btn_enter.click()
            time.sleep(2.5)

        # ---------------------------------------------------------------------
        # PHẦN 4: MỞ QUÁN ĂN ĐÊM (QUAN) — BẾP NẤU, BƯNG BÊ, PHỤC VỤ & TIỀN TIP
        # ---------------------------------------------------------------------
        print("🏮 Quán Ăn Chợ Nổi Má Tư lên đèn...")
        time.sleep(2.0)

        # Di chuyển đầu bếp trong quán (WASD)
        # Đi tới gần bếp B1 [2, 8]
        page.keyboard.down("a")
        page.keyboard.down("s")
        time.sleep(1.5)
        page.keyboard.up("a")
        page.keyboard.up("s")

        # Bốc món chín / tương tác bếp
        page.keyboard.press("e")
        time.sleep(1.5)

        # Đi tới các bàn ăn [9, 2], [13, 2], [9, 6]
        page.keyboard.down("d")
        time.sleep(2.0)
        page.keyboard.up("d")
        page.keyboard.press("e")
        time.sleep(2.0)

        # Phục vụ và nhận tiền tip
        page.keyboard.down("w")
        time.sleep(1.0)
        page.keyboard.up("w")
        page.keyboard.press("e")
        time.sleep(3.0)

        print("🛑 Hoàn tất kịch bản demo!")
        page.close()
        context.close()
        browser.close()

    # Tìm file webm do Playwright sinh ra
    recorded_files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith(".webm")]
    if not recorded_files:
        print("❌ Không tìm thấy file video webm!")
        return

    source_webm = recorded_files[0]
    print(f"📹 Đã ghi hình video nguồn: {source_webm}")

    # Chuyển đổi sang MP4 bằng ffmpeg
    print(f"🎬 Đang nén và chuyển đổi sang {FINAL_VIDEO} bằng ffmpeg...")
    cmd = [
        "ffmpeg", "-y", "-i", source_webm,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "22",
        FINAL_VIDEO
    ]
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(FINAL_VIDEO) / (1024 * 1024)
    print(f"✅ XUẤT VIDEO THÀNH CÔNG: {FINAL_VIDEO} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    record()
