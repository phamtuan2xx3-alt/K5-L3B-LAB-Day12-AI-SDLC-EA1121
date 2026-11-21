# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Nguyễn Thanh Tùng | Antigravity AI Assistant | Xây dựng logic DEV 1 (sinh tồn, oxy, ngạt, ngất) & tính năng áp suất nước sâu | ~25k tokens | AI xử lý so sánh dấu phẩy động biên depth > 18.0 bị lệch micro-step, sau đó sửa thành assertGreaterEqual |
| Phase 1 | Phạm Quang Tuấn | Antigravity AI Agent | Gameplay Hái & Bắt cá DEV 2, DOM HUD Dave the Diver, WebAudio SFX | ~120k tokens | AI ban đầu chưa tách delta thực tế của giỏ đồ trong UI; đã điều chỉnh theo Section 4 Research. |
| Phase 2 | Phạm Quang Tuấn | Antigravity AI Agent | Triển khai Contract v1.1, DaySim, Shop upgrades, Thủy quái Cá Sấu & Visuals mở rộng | ~160k tokens | AI nhầm lẫn `next_id` thay vì `new` trên IdAllocator và ban đầu dùng `BUTTONS_V10` trong InputPlayer; test suite đã phát hiện và sửa ngay. |
