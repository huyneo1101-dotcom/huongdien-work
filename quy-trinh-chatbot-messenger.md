# Quy trình trả lời tự động Messenger — Hương Diện Baby Mart

*Trạng thái: đã chốt quy trình 28/07/2026, CHƯA DỰNG. Đây là tài liệu tham chiếu khi bắt tay build.*

## Phạm vi

- **Kênh:** Inbox Messenger của fanpage **Hương Diện Baby Mart** (fanpage dùng chung cho cả 2 hộ kinh doanh: `huongdienbaby` MST 0100338642 và `hkdhuongdiendoquang` MST 001088004040). Không đụng comment công khai.
- **Văn phong:** bot trả lời **tự nhiên hoàn toàn bằng văn bản** (không dùng nút bấm quick-reply cứng như bản Manychat cũ).
- **Giới hạn cứng từ chính sách Meta — không phải kỹ thuật của mình:** bot chỉ được trả lời **chủ động trong vòng 24h** kể từ tin nhắn cuối của khách. Ngoài 24h, KHÔNG được tự gửi tin quảng cáo/khuyến mãi qua API thường — vi phạm chính sách Meta, dễ bị hạn chế/khoá fanpage. Muốn chủ động nhắc khuyến mãi cho khách cũ (ngoài 24h) phải qua **Sponsored Messages** (quảng cáo trả phí của Meta, chạy qua Ads Manager), không phải qua bot đang dựng. Việc quảng bá định kỳ cho khách cũ nên đẩy qua kênh khác (Zalo OA, email), không trông cậy vào Messenger.

## Nguồn dữ liệu

1. **FAQ / tư vấn theo tháng tuổi bé** — đã có sẵn nội dung ở [kich-ban-chatbot-theo-thang-tuoi.md](kich-ban-chatbot-theo-thang-tuoi.md) (viết cho Manychat, dạng nút bấm). Khi build: chuyển nội dung này thành system prompt / knowledge base cho Claude, giữ nguyên logic tư vấn (chào → hỏi tháng tuổi/cân nặng bé → gợi ý đúng size/sản phẩm → chốt), nhưng để Claude diễn đạt lại thành câu văn tự nhiên thay vì liệt kê nút bấm.
2. **Giá / tồn kho sản phẩm thật** — qua **KiotViet Public API** (Huy đang nâng gói Cao cấp 490k/tháng để mở). Tái dùng hạ tầng đã có: Supabase project `ltmlueqkajqmduoqghdf`, edge function `kiotviet-sync` (đang kéo số liệu bán hàng cho tab `Sales`) — kiểm tra lại xem có tái dùng trực tiếp được hay cần thêm 1 hàm mới chỉ để tra cứu giá/tồn theo tên sản phẩm.

## Luồng xử lý mỗi tin nhắn

1. **Webhook Messenger** (Facebook Developer App gắn vào fanpage Hương Diện Baby Mart) nhận sự kiện tin nhắn → gửi vào 1 Supabase Edge Function mới (cùng project `ltmlueqkajqmduoqghdf`).
2. **Bộ phân loại ý định** (gọi Claude API) xếp tin nhắn vào 1 trong 4 nhóm:
   - **FAQ tĩnh** (giá ship, giờ mở, đổi trả, địa chỉ, tư vấn theo tháng tuổi bé)
   - **Hỏi sản phẩm cụ thể** (giá/tồn kho một mặt hàng)
   - **Nhạy cảm** (khiếu nại, giá sỉ, đổi trả đã mua, mặc cả)
   - **Không chắc** (bot không đủ tin để tự trả lời)
3. Xử lý theo nhóm:
   - **FAQ tĩnh** → Claude trả lời ngay bằng văn bản tự nhiên, dựa trên nội dung tư vấn theo tháng tuổi + FAQ chung.
   - **Hỏi sản phẩm** → tra KiotViet API lấy giá/tồn kho thật → Claude soạn câu trả lời tự nhiên kèm số liệu thật.
   - **Nhạy cảm / Không chắc** → **không tự trả lời**. Bot gửi khách 1 câu giữ chỗ ("Shop sẽ phản hồi sớm ạ") + đẩy thông báo qua **bot Telegram `huongdien_bot`** (đã tạo) tới nhân viên/chủ xử lý tay.
4. **Van an toàn:** nếu bot tự trả lời quá 3 lượt liên tiếp cho cùng 1 khách mà khách vẫn hỏi tiếp → tự chuyển tay (báo `huongdien_bot`), tránh bot nói dai/nói sai kéo dài.
5. Log toàn bộ hội thoại + câu trả lời + nhãn phân loại vào 1 bảng Supabase mới (vd `hdw_messenger_logs`) để rà soát chất lượng định kỳ.

## 6 giai đoạn build

| Giai đoạn | Làm được gì | Điều kiện mở khoá |
|---|---|---|
| **Phase 1** | FAQ tĩnh (tư vấn theo tháng tuổi bé) + handoff nhân viên qua Telegram | Chỉ cần Facebook Developer App + Page Access Token — dựng được ngay |
| **Phase 2** | Thêm tra giá/tồn kho sản phẩm thật | Cần gói KiotViet Cao cấp active (đang nâng) |
| **Phase 3** | Hồ sơ khách hàng — nhớ thông tin bé (tháng tuổi, vấn đề sức khoẻ đã hỏi: táo bón, chậm tăng cân...) giữa các lần nhắn tin cách nhau nhiều ngày | Cần thêm bảng dữ liệu mới, làm sau khi Phase 1+2 chạy ổn |
| **Phase 4** | Gợi ý mua thêm / upsell dựa trên lịch sử mua hàng thật + hồ sơ khách hàng + khuyến mãi hiện có | Cần nối KiotViet theo từng khách (qua SĐT) + nguồn khuyến mãi (xem Phase 6 / tab HuongDienWork); làm sau Phase 2+3 |
| **Phase 5** | Phân khúc khách hàng theo hành vi chi tiêu (thoáng/chặt/trung bình) để tinh chỉnh cách gợi ý ở Phase 4 | Cần đủ lịch sử đơn hàng KiotViet để tính; làm sau Phase 4 |
| **Phase 6** | Đọc bài khuyến mãi trên Facebook Hương Diện → soạn đề xuất chương trình khuyến mãi → gửi Huy duyệt qua Telegram → sau khi duyệt mới ghi vào KiotViet | Cần kiểm tra KiotViet API có endpoint GHI khuyến mãi/bảng giá không; luồng riêng, tách khỏi bot trả lời khách |

### Phase 3 — Hồ sơ khách hàng (customer memory)

**Vấn đề:** trong 1 cuộc hội thoại, Claude tự thấy toàn bộ lịch sử tin nhắn nên đã "nhớ" được — không cần làm gì thêm. Nhưng giữa các lần khách quay lại hỏi cách nhau vài ngày/tuần, mỗi lần gọi Claude API là độc lập (stateless), nên cần tự lưu trữ ngoài để bot "nhớ" xuyên suốt.

**Cơ chế:**
1. Facebook cấp mỗi khách nhắn vào fanpage 1 mã cố định (PSID) — dùng làm khoá tra cứu, không cần khách đăng nhập gì thêm.
2. Thêm bảng mới trong Supabase (cùng project `ltmlueqkajqmduoqghdf` đang dùng), ví dụ `hdw_customer_profiles`: `psid`, tên bé, tháng tuổi/ngày sinh dự kiến, vấn đề sức khoẻ đã từng hỏi (mảng), sản phẩm đã quan tâm.
3. Mỗi tin nhắn mới đến → tra bảng theo PSID → đưa thông tin cũ vào ngữ cảnh cho Claude trước khi trả lời (vd: "khách này có bé 8 tháng, tuần trước hỏi về táo bón").
4. Khi Claude phát hiện thông tin mới trong hội thoại (tháng tuổi bé, vấn đề mới) → tự động ghi ngược lại bảng để lần sau dùng tiếp.

**Lưu ý riêng tư:** thông tin sức khoẻ trẻ em khá nhạy cảm — chỉ lưu tối thiểu cần thiết (không lưu thừa những gì không dùng tới), và cần biết rõ đang lưu gì nếu sau này có khiếu nại về quyền riêng tư.

**Bắt buộc về bảo mật (khác với các bảng khác của app):** `HuongDienWork` là app tĩnh chạy thẳng trên trình duyệt — mọi key nhúng trong `index.html` (như `SUPA_KEY` anon JWT đang dùng cho tab Sales) đều công khai, ai xem source cũng lấy được. Bảng `hdw_customer_profiles` KHÔNG được đi theo đường đó:
- Bật RLS, chính sách chặn hết với anon/publishable key.
- Chỉ Edge Function của webhook Messenger (chạy phía server) được đọc/ghi, dùng `service_role` key giữ trong secret của Edge Function — không bao giờ nhúng vào `index.html`.
- Chủ shop muốn xem hồ sơ khách từ app `HuongDienWork` thì phải qua 1 Edge Function riêng có xác thực, không query thẳng bảng bằng anon key.

### Phase 4 — Gợi ý mua thêm / upsell

**Cơ chế:** trước khi trả lời, ghép 3 nguồn vào ngữ cảnh cho Claude:
1. **Lịch sử mua hàng thật từ KiotViet** — mở rộng `kiotviet-sync` để tra theo khách cụ thể. Khách định danh trên Messenger bằng PSID, còn KiotViet định danh bằng số điện thoại — cần khách cung cấp SĐT (thường có sẵn khi từng đặt hàng) để nối 2 bên.
2. **Chương trình khuyến mãi hiện có** — cần 1 bảng cấu hình mới trong Supabase để Huy/nhân viên tự cập nhật khi có chương trình mới (KiotViet không tự cung cấp danh sách này).
3. **Hồ sơ khách hàng** (Phase 3) — tháng tuổi bé, vấn đề sức khoẻ đã hỏi, để gợi ý đúng lúc đúng nhu cầu (bé sắp qua giai đoạn ăn dặm → gợi ý đồ ăn dặm; đã hỏi táo bón mà chưa mua men vi sinh → gợi ý men vi sinh).

Claude chèn gợi ý mua thêm/upsell tự nhiên vào cuối câu trả lời chính, không phải quảng cáo cứng.

**Giới hạn tần suất:** chỉ gợi ý tối đa 1 lần/cuộc hội thoại, không nhồi vào mọi câu trả lời — tránh gây khó chịu cho khách.

### Phase 5 — Phân khúc khách hàng theo hành vi chi tiêu

**Không tính real-time** mỗi tin nhắn — tốn kém và không cần thiết. Chạy 1 tác vụ định kỳ (vd hằng tuần), đọc lịch sử đơn hàng KiotViet của từng khách, tính vài chỉ số đơn giản:
- Giá trị đơn hàng trung bình
- Có hay chọn hàng cao cấp hay luôn chọn rẻ nhất trong cùng loại
- Có mua khi không có giảm giá không

Gắn nhãn (**thoáng / chặt / trung bình**) vào hồ sơ khách hàng (bảng `hdw_customer_profiles` ở Phase 3). Bot ở Phase 4 chỉ cần đọc nhãn có sẵn khi trả lời — nhanh và rẻ, không phải phân tích số liệu thô mỗi lần.

### Phase 6 — Facebook → soạn đề xuất khuyến mãi → Huy duyệt → ghi KiotViet

**Luồng riêng, tách khỏi bot trả lời khách hàng** (chỉ phục vụ nội bộ chủ/nhân viên).

**Cơ chế:**
1. Đọc bài đăng khuyến mãi mới trên fanpage Hương Diện Baby Mart (qua Facebook Graph API).
2. Claude phân tích bài đăng, rút ra thông tin có cấu trúc: tên chương trình, sản phẩm áp dụng, mức giảm, ngày bắt đầu/kết thúc. **Bài đăng là văn bản tự do nên có thể đọc sai/sót** — đây là lý do bắt buộc phải qua bước duyệt (mục 3), không tự động ghi thẳng.
3. Gửi đề xuất qua Telegram (`huongdien_bot` đã có) cho Huy duyệt.
4. **Chỉ sau khi Huy duyệt** mới ghi vào KiotViet — qua API nếu KiotViet hỗ trợ ghi khuyến mãi/bảng giá (cần kiểm tra khi gói Cao cấp active, chưa xác nhận), hoặc nhân viên tự nhập tay theo đúng đề xuất đã soạn sẵn nếu API không ghi được.

**Nguyên tắc bắt buộc:** không bao giờ để bot tự ghi vào KiotViet trước khi duyệt — khuyến mãi/giá ảnh hưởng tiền thật lúc tính tiền ở quầy, duyệt trễ đồng nghĩa giá sai đã sống trong hệ thống.

## Kiểm định trước khi vận hành

Áp dụng cho **mọi phase**, không phải chỉ 1 lần lúc mới ra mắt — mỗi khi đổi FAQ/system prompt/thêm phase mới đều phải chạy lại bộ kiểm định này trước khi đưa ra dùng thật.

**Bước 1 — Dựng bộ ~100 câu hỏi kiểm định, gộp 2 nguồn:**
- **Trích từ lịch sử chat Messenger thật** (qua Meta Business Suite/Graph API) — phản ánh đúng cách khách Hương Diện thật sự hỏi. Bắt buộc: **ẩn danh** (bỏ tên, SĐT, địa chỉ cụ thể) trước khi đưa vào bất kỳ tài liệu nào — đặc biệt nhạy vì có cả thông tin sức khoẻ của bé; và **lọc chất lượng**, chỉ lấy đoạn nhân viên trả lời tốt làm mẫu, bỏ đoạn trả lời sai/dở.
- **Bổ sung câu tự tạo** (Claude soạn) cho các loại hiếm gặp trong lịch sử thật, đặc biệt câu nhạy cảm (khiếu nại/giá sỉ) — để chắc chắn có đủ ca kiểm tra dù thực tế ít gặp.
- Chia đều 4 loại theo đúng bộ phân loại ý định ở Phase 1: FAQ thường gặp, hỏi sản phẩm cụ thể, câu nhạy cảm (kiểm tra bot có **từ chối trả lời + chuyển nhân viên** đúng không — đây là chỗ hay sai nhất), câu mơ hồ/ngoài phạm vi.

**Bước 2 — Chạy thật qua bot đang dựng** (không phải tưởng tượng câu trả lời) để lấy câu trả lời thật của cấu hình hiện tại.

**Bước 3 — Huy (hoặc nhân viên rành nhất) chấm đúng/sai** từng câu; với câu sai thì viết lại câu trả lời đúng nên là gì.

**Bước 4 — Sửa ở gốc** (FAQ/system prompt), không vá riêng từng câu — để cả nhóm câu hỏi tương tự cùng được sửa theo.

**Bước 5 — Chạy lại toàn bộ bộ câu hỏi sau khi sửa** — kiểm không phá cái đã đúng trước đó.

**Bước 6 — Giữ bộ câu hỏi này làm bộ kiểm định lâu dài**, không dùng 1 lần rồi bỏ — chạy lại mỗi khi đổi FAQ/khuyến mãi/thêm phase mới.

## Checklist cần chuẩn bị trước khi bước sang dựng thật

- [ ] Facebook Developer App + Page Access Token + Webhook verify token cho fanpage Hương Diện Baby Mart
- [ ] Gói KiotViet Cao cấp active (Huy đang nâng)
- [x] Bot Telegram `huongdien_bot` đã tạo — cần lấy `chat_id` của nhân viên/chủ sẽ nhận thông báo
- [ ] Anthropic API key (billing) để edge function gọi Claude ở production
- [ ] (Phase 3) Tạo bảng `hdw_customer_profiles` trong Supabase — làm sau khi Phase 1+2 chạy ổn

## Điểm chưa quyết — cần Huy xác nhận lúc build

- Fanpage dùng chung 2 hộ kinh doanh: khi khách hỏi giá/tồn kho một sản phẩm, KiotViet có thể trả về theo gian hàng/kho của từng hộ khác nhau — cần biết lúc build là tra theo hộ nào, hay gộp chung không phân biệt.
