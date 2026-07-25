# Hương Diện · Quản lý công việc

Web app quản lý tiến độ công việc & học kiến thức kinh doanh cho chủ cửa hàng Mẹ&Bé Hương Diện.

Ứng dụng nằm gọn trong **một file `index.html`** (React + Babel + Tabler qua CDN, dữ liệu lưu `localStorage`). Mở thẳng trên trình duyệt, không cần cài đặt.

## Menu — 7 nhóm

| Nhóm | Tab con | Ai thấy |
|---|---|---|
| 🏠 **Tổng quan** | — | mọi người |
| ✅ **Công việc** | Hôm nay · Bảng việc · Theo mảng · Lịch·Hạn · Việc lặp lại | mọi người |
| 👥 **Đội ngũ** | Phân công · Tiến độ · Thành viên | chủ + quản lý |
| 📊 **Số liệu** | Bán hàng · Sổ KD · Thống kê | chủ + quản lý |
| 🏪 **Cửa hàng** | Nguồn hàng · Tuân thủ & Thuế | mọi người |
| 📚 **Cẩm nang** | Kiến thức · Sổ tay | mọi người |
| 🧠 **Não khỏe** | — | mọi người |

Nhân viên chỉ thấy 5 nhóm. Mở nhóm nào thì app nhớ tab con dùng lần trước.

## Tài khoản & phân công

Chủ cửa hàng tạo tài khoản cho từng người và chọn vai trò; app sinh **mã tạm 6 số**, người mới dùng mã đó đăng nhập lần đầu rồi **tự đặt mật khẩu riêng**. Chủ không biết mật khẩu của nhân viên, chỉ cấp lại được mã tạm mới.

Vai trò nạp sẵn: Chủ cửa hàng · Quản lý cửa hàng · NV Marketing & nhập hàng · NV chi nhánh ĐQ · NV bán hàng NK · NV kho & bắn đơn tỉnh. Thêm/xoá vai trò trong **Đội ngũ → Thành viên**.

Mỗi việc có người nhận. **Nhân viên chỉ thấy việc được giao cho mình** — to-do list riêng, và dữ liệu cá nhân (thói quen, năng lượng, bài đã học, kế hoạch ngày) tách riêng từng tài khoản. Chủ & quản lý thấy toàn bộ, lọc theo người ở thanh tab con.

> **Giới hạn bảo mật.** App chạy hoàn toàn trên trình duyệt, không có máy chủ kiểm tra đăng nhập. Màn khoá chặn người lạ mở link (họ không có tài khoản và không có dữ liệu) và người không phận sự cầm máy. Mật khẩu lưu dạng **băm SHA-256 kèm muối riêng**, không lưu chữ thật. Nhưng người rành kỹ thuật ngồi trước máy **đã đăng nhập** vẫn đọc được dữ liệu qua công cụ nhà phát triển — muốn chặn cả trường hợp đó phải chuyển sang tài khoản trên máy chủ (Supabase Auth + RLS). **Mã đồng bộ là chìa khoá vào dữ liệu cửa hàng từ máy khác — chỉ đưa cho người trong đội.**

**Tính năng khác:** Hôm nay (tự xếp ưu tiên, Deep Work, Pomodoro) · Bảng việc (Kanban) · Sổ kinh doanh (10 số/tuần) · Bán hàng (KiotViet) · **Nguồn hàng** · **Tuân thủ & Thuế** · Kiến thức (11 chủ đề) · Sổ tay (quy trình + thư viện prompt AI) · Việc lặp lại · Não khỏe · Nghỉ & Thở.

**Nguồn hàng** — theo dõi việc chuyển 24 thương hiệu nhóm A sang nhà phân phối chính thức tại VN: số điện thoại đã tra và xác minh, thứ tự gọi, bộ 9 câu hỏi bắt buộc, trạng thái từng brand và giá trị tồn kho đã chuyển được.

**Tuân thủ & Thuế** — danh sách rủi ro pháp lý đang có (bán thuốc, hàng xách tay, tem CR, quảng cáo sữa dưới 24 tháng…), bộ hồ sơ chứng từ theo lô, các thay đổi với hộ kinh doanh từ 2026, và lịch khai thuế quý kèm đếm ngược hạn nộp. App tự tạo việc làm tờ khai vào đầu mỗi tháng khai (1/4/7/10).

> Lưu ý: dữ liệu lưu cục bộ trên từng thiết bị/trình duyệt, không tự đồng bộ giữa máy. Dùng nút **Sổ tay → Sao lưu** để xuất/khôi phục.
