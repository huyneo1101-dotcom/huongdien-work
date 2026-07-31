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
   - **Bắt buộc xác minh chữ ký webhook**: mọi request Facebook gửi tới đều kèm header `X-Hub-Signature-256`, tính bằng HMAC-SHA256 của App Secret. Edge Function phải tự tính lại chữ ký từ body request và so khớp trước khi xử lý — không có bước này thì bất kỳ ai biết URL endpoint cũng giả mạo được tin nhắn/lệnh gửi vào hệ thống. App Secret giữ trong secret của Edge Function, không nhúng vào code commit.
   - **Gộp tin nhắn liên tiếp (debounce) trước khi phân loại**: khách thường gõ 2-3 câu ngắn liền nhau trong vài giây thay vì 1 câu dài (thói quen chat Messenger). Nếu mỗi tin gọi Claude riêng, bot trả lời rời rạc hoặc trùng lặp, và tốn thêm lượt gọi API không cần thiết. Cơ chế: mỗi khi có tin nhắn mới từ 1 khách, đặt hẹn giờ ngắn (khoảng 3-5 giây); nếu trong lúc chờ có thêm tin từ cùng khách thì gộp lại và reset hẹn giờ; hết giờ mới gộp toàn bộ thành 1 khối gửi cho Claude.
2. **Bộ phân loại ý định** (gọi Claude API) xếp tin nhắn vào 1 trong 5 nhóm:
   - **FAQ tĩnh** (giá ship, giờ mở, đổi trả, địa chỉ, tư vấn theo tháng tuổi bé)
   - **Hỏi sản phẩm cụ thể** (giá/tồn kho một mặt hàng)
   - **Gửi ảnh** (ảnh sản phẩm, ảnh đơn hàng lỗi, ảnh hóa đơn) — xem mục riêng bên dưới
   - **Nhạy cảm** (khiếu nại, giá sỉ, đổi trả đã mua, mặc cả)
   - **Không chắc** (bot không đủ tin để tự trả lời)
3. Xử lý theo nhóm:
   - **FAQ tĩnh** → Claude trả lời ngay bằng văn bản tự nhiên, dựa trên nội dung tư vấn theo tháng tuổi + FAQ chung. Dùng model nào (Haiku 4.5 hay Sonnet 5) tùy độ phức tạp câu hỏi — xem kiến trúc 3 tầng ở mục Chi phí bên dưới.
   - **Hỏi sản phẩm** → tra KiotViet API lấy giá/tồn kho thật → Claude soạn câu trả lời tự nhiên kèm số liệu thật.
   - **Gửi ảnh** → Claude (model có vision, xem mục Chi phí bên dưới) đọc ảnh trực tiếp qua Messenger attachment URL để mô tả/nhận diện sản phẩm trong ảnh; **KHÔNG tự kết luận** về ảnh hóa đơn/đơn hàng lỗi — luôn chuyển nhóm Nhạy cảm để nhân viên xem trực tiếp, vì đây là tình huống ảnh hưởng tiền/quyền lợi khách.
   - **Nhạy cảm / Không chắc** → **không tự trả lời**. Bot gửi khách 1 câu giữ chỗ ("Shop sẽ phản hồi sớm ạ") + đẩy thông báo qua **bot Telegram `huongdien_bot`** (đã tạo) tới nhân viên/chủ xử lý tay.
4. **Van an toàn:** đếm số lượt bot tự trả lời **liên tiếp không bị ngắt bởi tin nhân viên** cho cùng 1 khách trong cùng 1 phiên hội thoại (bộ đếm reset khi: nhân viên đã trả lời tay, hoặc khách im lặng quá 24h — hết phiên Messenger). Quá 3 lượt mà khách vẫn hỏi tiếp (không phải khách đã hài lòng rồi hỏi thêm chuyện mới) → tự chuyển tay (báo `huongdien_bot`), tránh bot nói dai/nói sai kéo dài.
5. **Giờ ngoài giờ làm việc:** bot vẫn tự trả lời FAQ tĩnh và tra giá/tồn kho 24/7 (không cần người). Với nhóm Nhạy cảm/Không chắc ngoài giờ làm (khai báo giờ mở cửa cụ thể lúc build), bot gửi câu giữ chỗ có ghi rõ "ngoài giờ làm, shop phản hồi vào giờ mở cửa" thay vì câu giữ chỗ ngụ ý phản hồi ngay — tránh khách chờ vô ích. Thông báo Telegram vẫn gửi bình thường, nhân viên xử lý khi vào ca.
6. Log toàn bộ hội thoại + câu trả lời + nhãn phân loại vào 1 bảng Supabase mới (vd `hdw_messenger_logs`) để rà soát chất lượng định kỳ.

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

**Quyền xóa hồ sơ:** khách có quyền yêu cầu xóa toàn bộ thông tin đã lưu về mình (tên bé, tháng tuổi, vấn đề sức khoẻ đã hỏi). Cần 1 đường xử lý yêu cầu này, không chỉ có đường ghi/đọc:
- Cách đơn giản nhất: khách nhắn 1 cụm cố định (vd "xóa dữ liệu của tôi") → bot nhận diện, xóa thẳng dòng `psid` đó khỏi `hdw_customer_profiles`, xác nhận lại với khách bằng 1 câu.
- Chủ/nhân viên cũng cần xóa được tay qua `HuongDienWork` khi khách yêu cầu qua kênh khác (điện thoại, trực tiếp tại shop) — thêm nút xóa hồ sơ vào màn hình xem hồ sơ khách (đã nêu ở mục bảo mật bên dưới, qua Edge Function riêng).

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

## Đã cân nhắc và loại: Meta Business Agent (bot AI miễn phí có sẵn của Meta)

Kiểm tra thật trên fanpage Hương Diện Baby Mart (31/07/2026, qua Hộp thư → nút "Meta Business Agent" → `business.facebook.com/latest/business_ai/instructions`): fanpage **đã có sẵn** tính năng này (đang tắt), miễn phí hoàn toàn, tích hợp thẳng Messenger, cấu hình qua các mục "Collect leads", "Complete an order", "Tone of voice", "Avoid certain topics" — không cần code, không cần Facebook Developer App.

**Huy chốt 31/07/2026: không dùng, xây thẳng bằng Claude API theo thiết kế 6 phase.** Lý do: Meta Business Agent chỉ làm được ngang Phase 1 (FAQ tĩnh, thu thập thông tin cơ bản, né chủ đề nhạy cảm) — không nối được KiotViet để tra giá/tồn kho thật, không làm được hồ sơ khách hàng theo tháng tuổi bé, không upsell, không phân khúc chi tiêu, không có luồng duyệt khuyến mãi. Dùng nó trước rồi chuyển sang Claude API sau sẽ phải làm lại từ đầu phần cấu hình + học lại hành vi khách, không đáng so với phần tiết kiệm ở Phase 1.

## Chi phí vận hành ước tính (Claude API)

Kiến trúc 2 tầng để tối ưu chi phí: **bộ phân loại ý định dùng Claude Haiku 4.5** ($1/$5 mỗi triệu token input/output — rẻ, đủ cho việc xếp loại đơn giản), **bước soạn câu trả lời tự nhiên dùng Claude Sonnet 5** ($3/$15 mỗi triệu token; đang có giá ưu đãi $2/$10 tới 31/08/2026) — cần chất lượng cao hơn Haiku vì phải tư vấn đúng, tự nhiên, không sai thông tin sức khoẻ trẻ em.

**Ước tính mỗi tin nhắn khách hỏi** (giả định: phân loại ~500 token vào + 20 token ra; trả lời ~2.000 token vào gồm FAQ/system prompt + 150 token ra):
- Phân loại (Haiku 4.5): ~$0,0006
- Trả lời (Sonnet 5, giá ưu đãi): ~$0,0055
- **Tổng ~$0,006/tin nhắn** (≈ 150 đồng/tin theo tỷ giá hiện tại)

**Lượng tin nhắn thực tế — đo được từ Meta Business Suite Insights (Hộp thư → biểu tượng Thông tin chi tiết), 28 ngày gần nhất (02/07–29/07/2026):**
- **1.143 lượt bắt đầu cuộc trò chuyện qua tin nhắn** (cả tự nhiên lẫn từ quảng cáo nhấn tin) → quy ra ~1.200 cuộc/tháng.
- Đây là số **cuộc trò chuyện**, chưa phải số tin nhắn — mỗi cuộc thường có 2-4 tin nhắn khách gửi qua lại (hỏi giá, hỏi thêm, hỏi tồn kho...). Quy đổi ra **~2.400-4.800 tin nhắn khách/tháng**.

**Chi phí Claude API/tháng ước tính theo số liệu thật trên:**

| Quy đổi | Số tin nhắn/tháng | Chi phí ước tính |
|---|---|---|
| Cận dưới (2 tin/cuộc) | ~2.400 | ~$14 (~350.000đ) |
| Cận trên (4 tin/cuộc) | ~4.800 | ~$29 (~725.000đ) |

Chưa tính Supabase/KiotViet — các dịch vụ đó nhiều khả năng vẫn nằm trong gói miễn phí ở quy mô này.

**Lưu ý:** hệ số "2-4 tin/cuộc trò chuyện" vẫn là giả định (Meta Insights không cho xem trực tiếp tổng số tin nhắn, chỉ cho xem số cuộc trò chuyện mới). Cần đo lại bằng `count_tokens` trên nội dung FAQ/system prompt thật lúc build để ra số chính xác hơn. Bật **prompt caching** cho phần FAQ/system prompt (nội dung cố định, chỉ đổi câu hỏi khách) có thể giảm thêm ~50-70% chi phí phần input — nên cân nhắc bật ngay từ Phase 1.

### Cách giảm chi phí thêm — kiến trúc 3 tầng thay vì 2 tầng

Bảng chi phí trên giả định **mọi** câu trả lời đều qua Sonnet 5. Thực tế phần lớn câu hỏi FAQ (giá ship, giờ mở, địa chỉ, chính sách đổi trả) là câu hỏi đơn giản có đáp án cố định — không cần mô hình mạnh để trả lời tự nhiên. Tách thêm 1 tầng:

- **Tầng 1 — Haiku 4.5**: phân loại ý định (như đã thiết kế).
- **Tầng 2 — Haiku 4.5**: trả lời luôn cho nhóm FAQ tĩnh đơn giản (giá ship, giờ mở, địa chỉ...) — không cần Sonnet, Haiku đủ tự nhiên cho câu trả lời ngắn có khuôn sẵn.
- **Tầng 3 — Sonnet 5**: chỉ dùng cho tư vấn phức tạp cần đúng và tự nhiên cao (tư vấn theo tháng tuổi/vấn đề sức khoẻ bé, gợi ý sản phẩm, các câu Haiku tự đánh giá không đủ tin để trả lời).

Ước tính nếu ~70% câu hỏi rơi vào Tầng 2 (Haiku) và ~30% rơi vào Tầng 3 (Sonnet): chi phí bình quân mỗi tin giảm còn khoảng **$0,003-0,004** (so với $0,006 ở phương án toàn Sonnet) — **giảm ~40-50%** tổng chi phí hàng tháng, tức còn khoảng **$9-17/tháng (~225.000-425.000đ/tháng)** theo lượng tin nhắn đã đo ở trên. Cộng thêm prompt caching thì còn thấp hơn nữa. Tỉ lệ 70/30 là ước lượng — cần đo lại bằng log thật sau khi chạy Phase 1 một thời gian rồi mới chốt ngưỡng chuyển từ Tầng 2 sang Tầng 3.

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
- [x] Gói KiotViet Cao cấp active — đo thật 31/07/2026 bằng gọi API `/products` qua `kv_api.py`: hộ HD114 trả 444 sản phẩm (retailer `huongdienbaby`), hộ DQ trả 639 sản phẩm (retailer `hkdhuongdiendoquang`). Client ID/Secret cả 2 hộ đã có sẵn trong `~/.config/api-keys.env`
- [x] Bot Telegram `huongdien_bot` đã tạo — `chat_id` đã lấy (cắm 30/07/2026 qua `cam-bot-chot-so.py`, ghi ở `/Users/Huy/Claude/.huongdien-bot`, 1 người nhận). Chatbot Messenger có thể tái dùng thẳng file config này, không cần cắm lại
- [ ] Anthropic API key (billing riêng — KHÔNG trừ vào gói Claude Code) để edge function gọi Claude ở production — script cắm: `App/HuongDienWork/cam-anthropic-key-hdw.py`
- [ ] (Phase 3) Tạo bảng `hdw_customer_profiles` trong Supabase — làm sau khi Phase 1+2 chạy ổn

## Điểm chưa quyết — cần Huy xác nhận lúc build

- **Fanpage dùng chung 2 hộ kinh doanh** (`huongdienbaby` và `hkdhuongdiendoquang`): khi khách hỏi giá/tồn kho một sản phẩm, KiotViet trả về theo gian hàng/kho của từng hộ khác nhau. Hai phương án cụ thể:
  - **Phương án A (đơn giản hơn, khuyến nghị cho Phase 1-2):** tra và gộp tồn kho của cả 2 hộ khi trả lời khách — khách chỉ quan tâm "còn hàng không", không cần biết hộ nào bán. Nếu giá 2 hộ chênh nhau thì báo giá thấp hơn hoặc báo khoảng giá.
  - **Phương án B (chính xác hơn, phức tạp hơn):** xác định khách thuộc khu vực/kênh nào (nếu 2 hộ tách theo địa lý hoặc theo dòng sản phẩm) rồi chỉ tra đúng hộ đó — cần Huy cho biết quy tắc phân chia thực tế giữa 2 hộ (theo khu vực giao hàng? theo ngành hàng? theo lịch sử khách từng mua?) thì mới định tuyến được.
  - Cần Huy chốt lúc build: dùng phương án nào, và nếu chọn B thì quy tắc phân chia 2 hộ là gì.
