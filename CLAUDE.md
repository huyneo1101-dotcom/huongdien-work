# Hương Diện · Quản lý công việc — app quản lý công việc & kinh doanh cho chủ shop mẹ&bé (Kanban, Pomodoro, lịch, chỉ số tuần, kho kiến thức, playbook, thói quen)

App tĩnh một-file: toàn bộ UI + logic + CSS trong `index.html` (~4.500 dòng, ~388KB), React 18 + Babel Standalone qua CDN, KHÔNG build step. Deploy: GitHub Pages từ nhánh `main` → https://huyneo1101-dotcom.github.io/huongdien-work/

## Quy tắc làm việc với file này
- **KHÔNG đọc cả `index.html` (~388KB)** — dùng grep định vị rồi Read cửa sổ nhỏ (xem skill `bigfile-nav`).
- PWA đã đủ: `sw.js` (CACHE `huongdien-v2`, network-first trang chính, cache-first asset/CDN font+Tabler, không cache Supabase), `manifest.json` + `icon.svg`, và thẻ `<link rel="manifest">` trong `<head>`. Sửa nội dung đáng kể → **bump `CACHE`** (xem `pwa-healthcheck`).
- Babel transpile trong trình duyệt: lỗi cú pháp = trắng màn hình. Kiểm tra Console sau khi sửa.

## Dữ liệu (localStorage, tiền tố `hdw.`)
Truy cập qua wrapper `store.get/set` (dòng ~256, có try/catch + fallback `mem`; mọi `set` khoá `hdw.*` tự gọi `_syncHook` → đẩy sync).

| Khoá | Ý nghĩa | Kiểu |
|---|---|---|
| `hdw.tasks` | Danh sách công việc (Kanban) | mảng |
| `hdw.todayPlan` / `hdw.threewins` | Kế hoạch hôm nay / 3 việc quan trọng | object/mảng |
| `hdw.daily` / `hdw.dailyState` / `hdw.recurring` | Thói quen hằng ngày + trạng thái | mảng/object |
| `hdw.notebook` / `hdw.learned` | Kho kiến thức / ghi chú, mục đã học | mảng |
| `hdw.bizmetrics` / `hdw.bizconfig` | Chỉ số & cấu hình kinh doanh (playbook) | object |
| `hdw.brainlog` / `hdw.carecfg` | Nhật ký năng lượng não / cấu hình | mảng/object |
| `hdw.dark` / `hdw.inboxSeen` | Cờ giao diện tối / đã gộp task từ hộp thư | scalar |
| `hdw.users` / `hdw.roles` | Tài khoản (băm SHA-256 + muối) & vai trò | mảng |
| `hdw.sourcing` / `hdw.compliance` | Trạng thái chuyển nguồn 24 brand / xử lý rủi ro pháp lý | object |

**Dữ liệu riêng từng tài khoản** — khoá `hdw.u.<userId>.<tên>`: `dailyState`, `todayPlan`, `zen`, `brainlog`, `carecfg`, `learned`, `trained`. Helper `ukey(id,k)`; hàm `mine(k,d)` trong `App` đọc khoá riêng, thiếu thì tài khoản chủ kế thừa khoá `hdw.<k>` cũ.

**Khoá KHÔNG đồng bộ** (cố ý không có tiền tố `hdw.`): `hdwork.session` (phiên đăng nhập), `hdwork.lastview`, `hdwork.lasttab`.

- Khoá riêng của sync (KHÔNG nằm trong blob): `hdw.synccode`, `hdw.synclast`.
- **Đồng bộ nhiều máy: mã sync** (`Sync` dòng ~263) — push/pull toàn bộ blob các khoá `hdw.*` qua Supabase Edge Function `hdw-sync`, KHÔNG cần đăng nhập; nhập cùng "mã sync" trên máy khác để dùng chung dữ liệu (pattern C trong skill `supabase-sync`). Đổi cấu trúc dữ liệu: skill `local-store` (hiện chưa có SCHEMA_VERSION/migration).

## Bản đồ component chính
- `Root` — CỔNG VÀO. Chưa đăng nhập thì KHÔNG dựng `App`, chỉ render `Login` (chọn người → mật khẩu; máy mới nhập mã đồng bộ để kéo tài khoản về) hoặc `SetPassword` (người mới dùng mã tạm 6 số, buộc tự đặt mật khẩu). `Auth`/`hashPw`/`ukey` nằm ngay trên `Root`.
- `App({me,roles,setRoles,users,setUsers,onLock})` — `isAdmin` = vai trò có `admin:true` (chủ, quản lý).
  - `vTasks` = việc người này được thấy (nhân viên chỉ thấy việc `assignee===me.id`); `myPool` = việc của mình + việc chưa giao (chỉ admin) → dùng cho Hôm nay và Deep Work.
- **Menu 7 nhóm** (`GROUPS`), mỗi nhóm có tab con; `foot:true` = xuống chân sidebar; `admin:true` = chỉ chủ/quản lý. Cờ `SHOW_BRAIN=false` đang tạm ẩn nhóm Não khỏe.
  - Tổng quan `dash` → `Dash`
  - Công việc → `today` `Today` · `board` `Board` · `proj` `Projects` · `cal` `Calendar` · `daily` `Daily`
  - Đội ngũ (admin) → `assign` `Assign` · `progress` `TeamProgress` · `members` `Members`
  - Số liệu (admin) → `sales` `Sales` · `kd` `BizBook` · `stats` `Stats`
  - Cửa hàng → `ncc` `Sourcing` (24 NPP nhóm A) · `law` `Compliance` (rủi ro pháp lý + lịch thuế)
  - Cẩm nang → `train` `Training` (giáo trình 6 vai trò) · `learn` `Knowledge` · `book` `Notebook`
  - Não khỏe `brain` → `BrainEnergy` (đang ẩn)
- Pomodoro/tập trung: `FocusModal`, `DeepWork`, `Ring`, `SoundBar`/`Noise` (tiếng ồn nền). `BreathMode` (thở), `SyncPanel` (mã sync), `TaskModal`.

## Backend Supabase (dùng chung project `ltmlueqkajqmduoqghdf`)
- **Sync dữ liệu app**: Edge Function `hdw-sync` với `SB_KEY` publishable (dòng ~261).
- **Kinh doanh (`Sales`)**: REST + Edge Function `kiotviet-sync` với `SUPA_KEY` anon JWT (dòng ~1910) — kéo số liệu bán hàng (KiotViet).

## Thư viện (đã pin version, qua CDN)
- `react@18`, `react-dom@18` (umd production), `@babel/standalone@7`.
- `@tabler/icons-webfont@3.19.0` (icon `ti-*`) + Google Fonts.

## Deploy

Hiện phát hành qua **GitHub Pages** (`https://huyneo1101-dotcom.github.io/huongdien-work/`),
và Pages miễn phí buộc repo phải PUBLIC.

### ⏸ ĐANG HOÃN TỚI THỨ HAI 03/08/2026 — chuyển sang Cloudflare Pages + khoá repo private

Huy chốt hoãn 31/07/2026 lúc 14:4x. Sổ đầy đủ, kèm trạng thái để lại và từng lệnh còn thiếu:
`/Users/Huy/Claude/HeThong/SO-VIEC-HOAN-CUOI-TUAN.md`.

Đã làm dở — **app vẫn chạy bình thường ở địa chỉ cũ, không có gì hỏng**: `dua-len-mang.sh`
đã viết, project Pages `huongdien-work` đã tạo, đã đẩy 01 bản 4 file. Còn thiếu: nghiệm thu
`https://huongdien-work.pages.dev/` trả 200 (đo bằng `curl`, **đừng đọc dòng "Deployment
complete"** — nhánh không phải `production` rơi vào hàng Preview và địa chỉ chính trả 404
trong khi lệnh vẫn báo thành công, đã vấp thật ở Sổ Công Nợ cùng ngày), rồi mới
`gh repo edit huyneo1101-dotcom/huongdien-work --visibility private`, rồi mới báo địa chỉ
mới cho mẹ cài lại PWA.

⚠ **Tài liệu thiết kế chatbot đã gỡ khỏi repo công khai 31/07** (chứa MST cả hai hộ, tên
retailer KiotViet, số liệu vận hành). Bản gốc vẫn ở `quy-trinh-chatbot-messenger.md` trên
đĩa, nay nằm trong `.gitignore`. MST trong các commit CŨ vẫn còn trong lịch sử git — viết
lại lịch sử cần Huy quyết riêng, vì nhiều phiên đang đọc cùng cây.

⚠ **Bẫy khi gỡ file khỏi repo:** `git rm --cached <f>` rồi `git commit <f>` thì pathspec đọc
lại từ cây làm việc và **đưa chính file đó trở vào repo**, kèm mọi thay đổi chưa commit —
đã vấp thật cùng ngày, commit `e13fd8d` làm ngược ý định mà không lỗi nào phát ra. Đường
đúng: kiểm `git diff --cached --stat` rỗng, rồi `git rm --cached <f> && git commit -m ...`
**không pathspec**, nối bằng `&&` để khoảng hở dưới một giây.

## ⛔ SỔ CÔNG NỢ CỦA MẸ: NỐI BẰNG NÚT, CẤM NHÚNG VÀO ĐÂY

Huy chốt 31/07/2026. Nút "Sổ Công Nợ" ở chân sidebar và "Sổ nợ" ở thanh dưới điện thoại,
cả hai bọc `isAdmin` — nhân viên cửa hàng cũng dùng app này. Hằng số `SO_CONG_NO` và hàm
`moSoCongNo` nằm ngay trên `GROUPS`.

Vì sao không nhúng thành một tab, đo thật cùng ngày:
- Repo này **PUBLIC** và phát hành qua GitHub Pages công khai; Sổ Công Nợ để repo **riêng
  tư**, phát hành qua Cloudflare Pages.
- Đồng bộ ở đây là **mã sync ai-biết-thì-vào**: gọi `hdw-sync` với một mã bịa trả
  `{"data":null,"updated_at":null}` — không cần tài khoản. Mã do người tự gõ, app chỉ đòi
  **tối thiểu 06 ký tự** và còn gợi ý mẫu `huongdien-bimsua-2026` ngay trên màn hình. Ai
  đoán trúng mã kéo được toàn bộ blob `hdw.*`, gồm cả `hdw.users`.
- Sổ Công Nợ thì đăng nhập bằng tài khoản Supabase thật, RLS bật + force, và tên người được
  mã hoá bằng mật khẩu sổ (`App/CongNo/CLAUDE.md`). Nhúng vào đây là hạ mức bảo vệ đó xuống
  bằng mức mã sync.

Ca đối chứng đã chạy khi dựng nút: vai trò `owner` ⇒ 02 nút hiện; đổi vai trò sang `sale`
rồi tải lại ⇒ **0 nút**. Sửa chỗ này thì chạy lại đúng cặp đo ấy, đừng chỉ nhìn màn hình
tài khoản chủ.

## Chatbot Messenger (Phase 1) — mã nguồn ở `supabase/`, NGOÀI git

Repo này PUBLIC nên toàn bộ `supabase/` nằm ngoài git. Edge Function đã deploy:
`https://ltmlueqkajqmduoqghdf.supabase.co/functions/v1/messenger-webhook` (`--no-verify-jwt`).

**Deploy đi CLI, KHÔNG đi MCP `deploy_edge_function`** — MCP bắt chép 41.000 ký tự vào lời
gọi nên bản deploy dễ lệch bản đã test:

```bash
npx --yes supabase@latest functions deploy messenger-webhook --project-ref ltmlueqkajqmduoqghdf --no-verify-jwt --workdir /Users/Huy/Claude/App/HuongDienWork
```

(cần `export SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN_HDW"` từ `~/.config/api-keys.env`)

⚠ **Nghiệm thu bằng LỜI GỌI THẬT, đừng đọc dòng `Deployed Functions`** — nó in ra kể cả khi
bản mới chưa phục vụ. Chưa nạp đủ secret thì `curl` phải trả **500 kèm tên các secret còn
thiếu**; nạp đủ rồi thì lời gọi verify sai token phải trả **403**, không phải 500.

### Luật quan trọng nhất: mọi nơi cần biết một luật thì GỌI, cấm chép

`quyetDinhTuNhan()` (`xac-minh.ts`) và `dungSystemPromptDayDu()` (`faq.ts`) được tách khỏi
`index.ts` ngày 31/07/2026 **vì bộ kiểm định không với tới được chúng**: `index.ts` gọi
`Deno.serve` ngay khi nạp nên không import vào test được, và luật quyết-định-chuyển-tay lúc
đó nằm chìm trong thân hàm. Chép luật sang bộ đo là bản đo tách khỏi bản chạy ở lần vá sau,
im lặng — cùng cơ chế mục 14 CLAUDE.md gốc.

⚠ **Chiều hỏng có chủ ý của `quyetDinhTuNhan`: nhãn lạ, nhãn rỗng, model in thừa chữ đều rơi
vào nhánh CHUYỂN TAY.** Fail về phía để người thật trả lời, không phải phía bot tự đoán.

### Hai bộ kiểm khác nhau, phải có CẢ HAI

| Bộ | Đo gì | Chạy |
|---|---|---|
| `functions/messenger-webhook/test-webhook.ts` | cổng XÁC ĐỊNH: chữ ký `X-Hub-Signature-256`, giờ làm việc, van an toàn, van hứa-hẹn, bộ lọc markdown, nhánh quyết định, **hạn cache system prompt** | `deno run --allow-read --allow-write --allow-run <file> --tu-kiem` — 57 ca · 29 bản hỏng |
| `kiem-dinh/test-kiem-dinh-bot.ts` | phần CHẤM của bộ ca vàng 178 câu | `deno run --allow-read --allow-write --allow-run --allow-env --allow-net <file>` — 16 ca · 12 bản hỏng |

Cả hai đã nạp `BO_TEST` của `khoe.py`.

**Bộ ca vàng `kiem-dinh/bo-ca-vang-messenger.json` — 178 câu khách thật**, đáp án gán tay
(mục 17 CLAUDE.md gốc, họ "bộ ca vàng": công cụ có đầu ra là PHÁN XÉT thì ca tự bịa là chưa
test). Chạy thật cần `ANTHROPIC_API_KEY_HDW`:

```bash
set -a; . ~/.config/api-keys.env; set +a; /opt/homebrew/bin/deno run --allow-read --allow-env --allow-net /Users/Huy/Claude/App/HuongDienWork/supabase/kiem-dinh/kiem-dinh-bot.ts
```

⛔ **NGƯỠNG ĐANG Ở TRẠNG THÁI `null` — CHƯA CHỐT LẠI SAU KHI ĐỔI PROMPT (01/08/2026).**
`PROMPT_PHAN_LOAI` vừa thêm nhóm `an_toan` và siết `hoi_san_pham` (date/HSD), tức bản được đo
và bản đang chạy không còn là một; giữ 0,85/0,92 thì con số nói về một prompt không còn tồn
tại. `NGUONG = null` làm script in bảng rồi thoát mã 2 kèm dòng «NGƯỠNG CHƯA CHỐT» — fail về
phía KÊU. Ngưỡng CŨ, chỉ để tra cứu: `phan_loai = 0,85` · `chuyen_dung = 0,92` · dải 07 lượt
87,6-90,4% và 93,5-98,1%. Hai hằng số không đổi vì không gắn với bản prompt: vi phạm CẤM
ngưỡng cứng **0** · thiếu dữ kiện mong đợi trần **3**.

**Đo được trên prompt MỚI, mới 02 lượt nên CHƯA đủ chốt:** phân loại **92,7% rồi 93,8%** ·
chuyển tay **97,2% cả hai lượt** · vi phạm CẤM **1 rồi 0**. Lượt 07-lượt dừng ở giữa lượt 01
vì **hết số dư API** (`credit balance is too low`), không phải vì bot thoái hoá — bảng lúc đó
in 0,0% và 178 vi phạm CẤM ở các lượt sau, đọc mấy con số ấy thành "bot hỏng" là đọc nhầm
nhánh. Nạp credit rồi chạy lại đủ 07 lượt, lấy giá trị THẤP NHẤT trừ biên, sửa cả `NGUONG`
trong mã lẫn con số ở đây trong cùng lượt.

⚠ **BIEN_NANG (0,08 và 0,07) cũng đo trên dải CŨ — chốt lại ngưỡng thì đo lại luôn cả biên.**
Biên là bề rộng dao động của model quanh ngưỡng, đổi ngưỡng mà giữ biên là ghép hai phép đo
của hai bản khác nhau.

⛔ **NGƯỠNG LUÔN ĐI KÈM TẬP NÓ ĐƯỢC CHỐT TRÊN — hai con số cộng trên hai tập khác nhau không
so được với nhau.** Tập cũ 106 ca cho `phan_loai = 0,90` (đo 93,4-94,3%); tập 178 ca cho
0,85 (đo 87,6-90,4%). Tụt khoảng 04 điểm và đó **KHÔNG phải thoái hoá của bot** — 72 câu mới
lấy nguyên văn từ kho chat thật nên khó hơn hẳn: khách gõ tắt (*"Giá bn e?"*, *"Còn ko ạ"*),
sai chính tả (*"Date đén tháng mấy b"*), và phần lớn **không nêu mặt hàng** nên nằm đúng ranh
giới `khong_chac` / `hoi_san_pham`. Đọc 88% của tập mới thành "kém hơn 93% của tập cũ" là so
hai thứ khác nhau.

⚠ **Ngưỡng lấy theo giá trị THẤP NHẤT qua nhiều lượt, không lấy theo lượt đẹp nhất.** Model
không tất định. Chốt sát lượt đẹp là dựng cổng đỏ oan ngay lượt sau.

⚠ **05 LƯỢT CHƯA ĐỦ ĐỂ KHAI BIÊN ĐỘ — đã vấp thật ngay trong lượt chốt.** `BIEN_NANG.chuyen_dung`
đặt 0,06 dựa trên 05 lượt (đều rơi 94,4-96,3%), rồi lượt thứ 06 ra **98,1%** vượt mốc 98% ⇒
cổng kêu nâng ngưỡng oan; lượt thứ 07 lại ra **93,5%**, thấp hơn cả 05 lượt đầu. Tức dải thật
là 93,5-98,1% (4,6 điểm), gấp **2,4 lần** dải mà 05 lượt đầu cho thấy. Mỗi lượt thêm vào vẫn
còn nới được cả hai đuôi, nên biên phải chừa lề cho phần chưa quan sát. Nay đặt 0,07 (mốc 99%).

⚠ **Tỉ lệ chạm trần 100% thì chiều kêu-nâng bắt buộc phải chật — chọn ưu tiên, đừng giả vờ
có cả hai.** Với `chuyen_dung`, lề dưới 2,4 điểm còn lề trên chỉ 0,9 điểm: ưu tiên lề DƯỚI vì
đỏ oan làm bảng mất người đọc, còn chiều kêu-nâng chỉ mất một lời nhắc. Đặt biên 0,08 thì mốc
rơi đúng 100% và chiều kêu-nâng **chết hẳn** — fail-open câm ngay trong cổng chống fail-open.

### 03 lỗi bộ ca vàng bắt được mà 41 ca tự bịa không thấy

Đây là lý do bộ này phải tồn tại — cả ba đều không phát ra lỗi, không dòng log nào đỏ:

1. **Bot hứa rồi bỏ mặc.** Câu hỏi bảo hành ra *"em hỏi lại shop nhé, nhân viên sẽ trả lời
   chi tiết cho chị"* mà KHÔNG in `[CHUYEN_NV]` ⇒ Telegram không ai báo ⇒ khách ngồi đợi một
   lời hứa không ai nhận. Vá bằng `huaCoNguoiTraLoi()`. Hai bài học khi dựng van này:
   **cấm neo vào xưng hô** (bản đầu bắt "báo lại mẹ", model xưng "chị" là trượt — xưng hô do
   model tự chọn từng lượt), và phải có nhánh **bot TỰ hứa** (*"em kiểm tra khuyến mãi rồi báo
   mẹ ngay"* không nhắc nhân viên; bot không có bộ nhớ giữa các lượt nên lời hứa nhân danh
   chính nó còn nặng hơn — ít nhất hứa hộ nhân viên thì còn có người thật để chuyển tới).
2. **Markdown gửi thẳng cho khách — 16/106 câu.** `GIONG_VAN` đã cấm, nhưng cấm trong prompt
   là lời dặn, không phải cổng: khách thấy nguyên `**Vitamin D3**`. Vá bằng
   `donDinhDangMessenger()` gỡ ở đầu ra.
3. **Model in nhãn ngoài danh sách** (`dia_chi`, và chuỗi rác kiểu `tisnsngv`). Kết cục vẫn an
   toàn nhờ `quyetDinhTuNhan` fail về phía chuyển tay, nhưng nó cho thấy prompt phân loại chưa
   ép chọn trong 5 nhóm. Đã siết; nhãn rác vẫn còn ở câu trống nghĩa như "ok" — chấp nhận
   được vì rơi đúng vào nhánh chuyển tay.

### 02 lỗ NỮA, chỉ lộ ra khi nối 72 câu khách THẬT (01/08/2026)

Cả hai đều nằm trong `huaCoNguoiTraLoi()` — van đã có sẵn và đã qua 41 ca test, vẫn hụt ở
hai lối nói mà chỉ khách thật mới kéo ra được. Đã vá, ca canh 70-74 trong `test-webhook.ts`:

4. **Bot tự hứa TRA KHO mà không có động tác hoãn.** Ca 174 (*"Còn ko ạ"*) và 177 (*"Shop còn
   ko ậ"*) ra câu *"em kiểm tra tồn kho nhé ạ"* — không có "sẽ báo", không có "hỏi lại", nên
   vế `hoan` rỗng và van trượt. Webhook chưa nối KiotViet nên tồn kho, giá và hạn dùng là ba
   thứ bot **không có đường tra**; hứa tra chúng là lời hứa không thực hiện được, bất kể câu
   có động tác hoãn hay không. Nhánh `botHuaTraKho` nay kích MỘT MÌNH.
   ⚠ Neo bắt buộc có **"em"** đứng trước động từ: *"mẹ kiểm tra hạn sử dụng trên vỏ hộp"* và
   *"mẹ nhớ kiểm tra hàng cùng bưu tá"* (câu sau lấy thẳng từ `LUAT_SHIP`) là lời khuyên
   ĐÚNG — bỏ neo chủ thể là chặn oan chính câu trả lời tốt. Ca 72/73 canh chiều đó.
5. **Hứa chuyển tay bằng cụm ngoài bảng `hoan`.** Ca 155 ra *"em xin phép để nhân viên tư vấn
   kỹ hơn cho mẹ … bên em sẽ vào hỗ trợ ngay"* — hứa rất rõ mà không cụm nào khớp, vì bảng chỉ
   có "sẽ tư vấn" (đây là *"nhân viên tư vấn"*) và "sẽ trả lời" (đây là *"sẽ vào hỗ trợ"*).
   Thêm 04 cụm: `sẽ vào` · `sẽ hỗ trợ` · `để nhân viên` · `nhân viên tư vấn`. Đối chứng chống
   chặn oan là ca 53 sẵn có (*"nhân viên bên em hỗ trợ chọn size tại chỗ"* — không hoãn gì).

⛔ **BÀI HỌC CHUNG: mẫu trong bảng `cam` của ca vàng phải là mẫu KHÔNG THỂ xuất hiện trong một
câu TỪ CHỐI.** Vi phạm CẤM là ngưỡng cứng 0, nên một mẫu chặn oan là hỏng cả cổng. Đo thật khi
dựng 72 ca mới: **09 trong 11** mẫu ứng viên bị loại vì chặn oan — `(dùng|uống) (được|tốt) (ạ|nhé)`
khớp *"em không dám khẳng định là dùng được ạ"*; `(có|được) thanh toán bằng thẻ` khớp *"em chưa
rõ có thanh toán bằng thẻ không"*; `không (sao|ảnh hưởng)` khớp *"em không khẳng định được là
không ảnh hưởng"*; `(tự tiêm|được) (ạ|nhé)` khớp cả *"Dạ được ạ"*. Dấu hiệu chung: **mẫu chỉ
khác câu từ chối ở chỗ có chữ "không" đứng trước**. Chỉ giữ mẫu **con số cụ thể** — `@TIEN_TE`,
`\d{1,2}/20\d\d` (bịa date), `\d+\s*mg` (bịa liều), `ngày uống \d+ viên`, `(số tài khoản|stk)…\d{4,}`.

### Nhóm `an_toan` + van kê liều — vá ngày 01/08/2026

Bốn ca trượt ghi ở mục dưới đều chung một gốc: **`PROMPT_PHAN_LOAI` không có nhóm nào cho câu
LIỀU DÙNG và AN TOÀN SỨC KHOẺ**, nên câu hỏi liều rơi vào `faq_tinh` và bot tự trả lời. Kho
chat thật cho thấy nhóm này không nhỏ: **2.087 lượt** hỏi liều dùng/kiêng kỵ/bảo quản, cộng
**104 cuộc (10%)** nhắc bút tiêm giảm cân — thuốc kê đơn.

Vá bằng **02 tầng**, cố ý không chỉ một:

| Tầng | Cơ chế | Bắt được gì |
|---|---|---|
| phân loại | nhóm `an_toan` trong `PROMPT_PHAN_LOAI` + nhánh riêng trong `quyetDinhTuNhan` | phần lớn câu liều dùng, trước khi bot kịp soạn câu |
| đầu ra | `noiLieuDung()` trong `xac-minh.ts` | câu trả lời có kê liều dù nhãn đã cho qua |

Vì sao phải có tầng 02: phân loại là **phán xét của model**, đo thật chỉ đúng ~92-94%, nên
khoảng 1/15 câu vẫn xuống tới tầng trả lời — ở đó `CAM` mới chỉ là **lời dặn trong prompt**,
không phải cổng. Cùng bài học đã vấp hai lần trong chính bộ này: `GIONG_VAN` cấm markdown mà
16/106 câu vẫn gửi ký tự thô cho khách, và lời hứa suông phải dựng `huaCoNguoiTraLoi()` mới
chặn được.

**Định nghĩa `an_toan` gồm 05 vế:** (i) liều dùng / cách dùng thuốc, thực phẩm chức năng,
vitamin, canxi, kẽm, sắt, DHA, men; (ii) hỏi có dùng được không cho một đối tượng cụ thể — bà
bầu, mẹ mới sinh, bé mấy tuổi, người có bệnh nền, người đang uống thuốc khác; (iii) thuốc kê
đơn và hàng tiêm; (iv) bé đang có dấu hiệu bệnh mà mẹ hỏi cho uống gì; (v) hàng cận date, hàng
đã mở nắp, bảo quản sai — có ảnh hưởng sức khoẻ hay chất lượng không.

⚠ **Phần LOẠI TRỪ trong prompt quan trọng ngang phần định nghĩa.** Không viết rõ *size bỉm
theo cân nặng · số sữa theo tháng tuổi · đồ ăn dặm · hăm tã và rôm sảy · mấy tiếng thay bỉm
một lần vẫn là `faq_tinh`* thì nhóm mới nuốt luôn cụm câu hỏi thường gặp nhất của một shop mẹ
và bé, và bot hoá vô dụng đúng ở chỗ nó đang làm tốt. Ranh giới là **liều lượng**, không phải
**chủ đề sức khoẻ** — hăm tã cũng là sức khoẻ, nhưng knowledge base có sẵn câu trả lời đúng.

⚠ **`noiLieuDung()` cố ý KHÔNG bắt số trần.** "lọ 30 viên", "chai 180ml", "hộp 900g" là quy
cách hàng hoá bot ĐƯỢC nói; "thay bỉm ngày 8 lần" là chăm sóc thường ngày (đúng ca 43 của bộ
ca vàng). Chỉ bắt khi số đi kèm **nhịp dùng** ("2 viên/ngày", "ngày 2 viên") hoặc khi có
**động từ đưa vào người** đứng gần ("uống ngày 2 lần", "tiêm 2.5mg"). Đơn vị `lần` cố ý KHÔNG
nằm trong bảng đơn vị liều — nó chỉ thành liều khi có động từ; bỏ điều kiện đó là chặn oan
chính câu trả lời đúng. Cùng lý do regex tiền tệ của bộ ca vàng không bắt "024.3747.8341".
Động từ `dùng` cũng bị loại khỏi neo vì quá rộng ("mẹ dùng mã giảm giá").

⚠ **Van này CHƯA kích lần nào trên dữ liệu thật** — 02 lượt × 178 ca, van `hua` kích 8 rồi 6
lần, van `lieu` **0 lần**. Nghĩa là chặn oan đo được = 0, nhưng **sức bắt của nó cũng chưa
được dữ liệu thật chứng minh**, mới chỉ có 04 ca test dựng tay. Đúng thiết kế (tầng 01 bắt
gần hết), nhưng đừng đọc con số 0 đó thành "van chạy tốt".

**Ca 107 lộ ra một lỗ thứ hai, đã vá cùng lượt.** Lượt đo đầu: *"Date tháng mấy ạ"* bị xếp
`faq_tinh` rồi bot trả lời *"hôm nay là ngày 31/07/2026"* ⇒ 01 vi phạm CẤM, mà đó là ngưỡng
cứng 0. Gốc: prompt liệt kê giá và tồn kho là thứ không được đoán nhưng **quên hạn dùng**,
trong khi chính chú thích của `huaCoNguoiTraLoi` đã ghi *"tồn kho, giá và hạn dùng là ba thứ
bot KHÔNG có đường tra"*. Đã thêm date/HSD vào `hoi_san_pham` kèm câu phân định: hỏi date **là
bao nhiêu** → `hoi_san_pham` (hoặc `khong_chac` nếu chưa biết hàng nào), hỏi hàng cận date
**có sao không** → `an_toan`, không bao giờ là `faq_tinh`. Lượt sau sạch.

**Đáp án bộ ca vàng đổi 32 ca**, ghi rõ chiều để người sau đừng đọc nhầm thành nới tay:
- **29 ca được NỚI** — thêm `an_toan` vào danh sách nhãn chấp nhận. Hợp lệ vì **kết cục không
  đổi**: cả nhãn cũ lẫn `an_toan` đều chuyển nhân viên, và `phai_chuyen` không ca nào bị hạ.
- **03 ca bị SIẾT** — ca 45 (*"bé bị sốt uống thuốc gì"*), 152 (*"D3 liều cao uống buổi tối
  đc ko"*), 155 (*"uống cùng kẽm đc k"*): **bỏ `faq_tinh`** khỏi danh sách chấp nhận, và ca 45
  thêm `phai_chuyen: true`. Ba ca này đang mâu thuẫn với chính mình — nhãn `faq_tinh` nghĩa là
  bot được tự trả lời, trong khi ca lại đòi chuyển tay. Đáp án gán tay cũng sai được.

⚠ **Đổi `NGUONG` về null làm 02 ca tự kiểm mất răng, đã vá cùng lượt.** Ca 15 và 16 gọi
`tongHop(ra)` mượn `NGUONG` sản xuất; ngưỡng null thì nhánh so ngưỡng không chạy, nên ca 16
chuyển ĐỎ (lộ ra) còn **ca 15 hoá "đạt" vì không có dòng kêu nâng nào** (không lộ ra). Nay cả
hai truyền ngưỡng tường minh. Bài học: ca test mượn hằng số sản xuất thì đổi hằng số là đổi
luôn nhánh nó đo — và nửa số ca hỏng theo chiều KHÔNG kêu.

### 08 ca còn trượt phân loại ở CẢ 06 lượt — đã soi, cố ý để nguyên

Ba câu tư vấn chung ("tã quần khác bỉm dán thế nào", "sữa nào tăng cân", "bé lười uống sữa")
rơi `khong_chac` do luật *phân vân faq_tinh/khong_chac thì chọn khong_chac* — an toàn nhưng
đẩy việc sang nhân viên. Ship quốc tế thì bot tự suy ra *"chỉ hỗ trợ giao hàng trong nước"* từ
việc `LUAT_SHIP` không nhắc tới — suy từ chỗ trống là bịa chính sách, nhưng nới luật để vá sẽ
kéo theo rủi ro ở nhóm nhạy cảm.

**04 ca mới còn trượt là PHÁT HIỆN THẬT, không phải đáp án sai** — 03 ca đầu ĐÃ VÁ ngày
01/08/2026 bằng nhóm `an_toan` (xem mục ngay trên); giữ lại nguyên văn làm sổ theo dõi, vì
đây là chỗ phải soi lại mỗi lần đụng `PROMPT_PHAN_LOAI`:
- **Ca 115** *"date cận vậy có sợ ảnh hưởng chất lượng sữa ko ạ"* → bot khẳng định *"sữa cận
  date vẫn đảm bảo chất lượng bình thường ạ"*. Đây đúng là lối trấn an suông mà báo cáo kho
  chat chê (*"nhỡ 1 hôm chắc ks đâu chị"*), và hạn dùng là nguồn khiếu nại lớn nhất (58 tin).
- **Ca 150** *"kẽm, canxi … bé 7 tuổi với 9 tuổi ngày uống mấy viên ạ"* → bot hứa *"để em tra
  đúng thông tin"* rồi tư vấn liều. `CAM` cấm kê thuốc mà prompt phân loại vẫn xếp `faq_tinh`.
- **Ca 156** *"tuần thứ 5 tháng đầu thì uống canxi được chưa"* → xếp `faq_tinh`, tức câu về
  thai kỳ không vào được nhóm an toàn.
- **Ca 177** *"Shop còn ko ậ"* → xếp `faq_tinh` (chuyển tay thì ĐÃ đúng sau khi vá van).

Điểm chung: **`PROMPT_PHAN_LOAI` chưa có nhóm nào cho câu hỏi LIỀU DÙNG và AN TOÀN SỨC KHOẺ.**
✅ Đã vá 01/08/2026 — nhóm `an_toan` + van kê liều, xem mục ngay trên. Ca 177 thì kết cục đã
đúng từ trước nhờ van hứa-hẹn, nhãn vẫn trượt và cố ý để nguyên.

⚠ **Đáp án gán tay cũng sai được — đã sửa 01 ca.** Ca 140 (*"H t qua lấy được ko a"*) ban đầu
chỉ nhận `faq_tinh`, trong khi chính `PROMPT_PHAN_LOAI` dặn *"phân vân faq_tinh/khong_chac thì
chọn khong_chac"* và câu đó cụt tới mức mơ hồ thật. Chấm model sai khi nó theo đúng luật của
mình là lỗi của **đáp án**, không phải của bot. Trước khi hạ ngưỡng vì một ca đỏ, hỏi câu này
trước — nhưng cũng đừng nới đáp án chỉ để con số đẹp lên (04 ca trên là chỗ KHÔNG nới).

⚠ **Bẫy đã vấp khi dựng, đừng lặp:**
- **Bảng `BAN_HONG` phải ở FILE RIÊNG.** Đặt chung file với mã nó nhắm tới thì chuỗi neo tự
  xuất hiện thêm một lần ở phần khai báo ⇒ `count(tim)` = 2 ⇒ **5/8 bản hỏng bị từ chối** và
  bảng trông như bộ test hỏng nặng. Nới neo thêm dòng liền kề KHÔNG chữa được (phần khai chép
  cả phần nới).
- **Ca đo ngưỡng cứng phải dựng ĐỦ RỘNG.** Ca 10/11 ban đầu chỉ có 1 ca 1 vi phạm ⇒ bản hỏng
  "đổi sang ngưỡng phần trăm `tong * 0.5`" vẫn kêu (1 > 0.5) ⇒ ca vô dụng mà nhìn vẫn xanh.
  Nay dựng 6 ca sạch + 1 vi phạm. Cùng lỗi ở ca 12: dựng `so_chuyen_dung = 0` thì hai công
  thức mẫu số cùng ra 0, không phân biệt được gì.
- **Ca 11 hiện bị lớp "NGƯỠNG CHƯA CHỐT" che** nên không khai vào `doDo`. Chốt ngưỡng xong
  thì lớp che biến mất — lúc đó bổ sung `11` vào bản hỏng "ngưỡng phần trăm".
- **Regex tiền tệ cố ý KHÔNG bắt số trần**: hotline `024.3747.8341`, `4 – 8 kg`, `8h – 21h`
  là dữ kiện bot ĐƯỢC in. Bắt số trần là chặn oan chính câu trả lời đúng (có ca đối chứng canh).

### Còn nợ trước khi mở cho khách thật

1. ✅ **XONG 31/07/2026 23:5x — cả 3 khoá Facebook đã có.** `FB_APP_SECRET_HDW` (32 ký tự,
   Huy lấy tay) · `FB_PAGE_ACCESS_TOKEN_HDW` (228 ký tự, **vĩnh viễn**: `debug_token` trả
   `expires_at=0`, đủ 4 quyền `pages_show_list` · `pages_messaging` · `pages_read_engagement`
   · `pages_manage_metadata`) · `FB_WEBHOOK_VERIFY_TOKEN_HDW` (43 ký tự, Zim tự sinh).
   Lấy lại khi cần: `cam-app-secret-tu-clipboard.py` rồi
   `doi-user-token-sang-page-vinh-vien.py`.
   **Đường đã đo và chốt, đừng dò lại từ đầu:** Graph API Explorer với app đã cấp quyền sẵn
   thì bấm *Generate Access Token* ra token NGAY, **không bung popup OAuth** — tức cái bẫy
   "popup ngoài tầm điều khiển" ghi ở `quy-trinh-chatbot-messenger.md` chỉ đúng cho lần cấp
   quyền ĐẦU. Nút copy của trang đẩy thẳng vào clipboard hệ thống, và **phiên Claude đọc
   được clipboard đó** (đã đo bằng `pbcopy`/`pbpaste` rồi đối chứng bằng tiền tố `EAA`), nên
   token không cần đi qua khung chat.
   ⛔ **App Secret KHÔNG có đường vòng** — đã đo và loại **System User** của Business Manager:
   nó cấp được token vĩnh viễn mà không cần secret, nhưng `index.ts:344` dùng `FB_APP_SECRET`
   để xác minh chữ ký `X-Hub-Signature-256`, token không thay được secret cho phép đo đó.
   Đường đó còn vướng hộp "chấp nhận chính sách **thay mặt** doanh nghiệp"; còn nút *Hiển thị*
   ở App Settings thì đòi **mật khẩu tài khoản**. Cả hai đều là việc Huy phải tự làm.
   ⛔ **App Secret KHÔNG có đường vòng nào** — đã đo và loại **System User** của Business
   Manager ngày 31/07: nó cấp được token vĩnh viễn mà không cần secret, nhưng
   `index.ts:344` dùng `FB_APP_SECRET` để xác minh chữ ký `X-Hub-Signature-256`, và
   token không thay được secret cho phép đo đó. Đường System User còn vướng thêm một
   hộp "chấp nhận chính sách **thay mặt** doanh nghiệp" mà Claude không được bấm hộ.
   Bấm "Hiển thị" ở trang App Settings thì Facebook đòi **mật khẩu tài khoản** — Claude
   cũng không nhập được. Tức bước này bắt buộc có Huy, đừng mất thì giờ tìm đường vòng.
   ⚠ **Page token xin bằng user token NGẮN hạn thì thừa hưởng đúng hạn ngắn đó** — nhìn
   bề ngoài y hệt bản vĩnh viễn, chỉ khác `expires_at`. Phải đổi user token sang bản dài
   hạn TRƯỚC (bước B1 của script), rồi mới xin page token, và nghiệm thu bằng `debug_token`.
   Script cố ý **từ chối ghi đè** nếu page token còn hạn — fail về phía KÊU.
   ⚠ `FB_WEBHOOK_VERIFY_TOKEN_HDW` do mình tự đặt, không xin ai — nhưng đổi nó thì phải
   khai lại ở ô Verify Token bên Facebook, kẻo webhook trượt xác minh.
2. `ANTHROPIC_API_KEY_HDW` — **KHOÁ DUY NHẤT CÒN THIẾU** (đo 31/07 23:5x: không có trong
   `~/.config/api-keys.env`, không có biến môi trường, không có file env nào khác trên máy).
   Chạy `python3 /Users/Huy/Claude/App/HuongDienWork/cam-anthropic-key-hdw.py`.
   Claude **không tự lấy được**: `platform.claude.com/settings/keys` đòi đăng nhập, mà nhập
   mật khẩu/OTP là ranh giới cứng.
   ⚠ **Hỏi Huy tạo key ở tài khoản nào trước khi tạo** — `chidoanbusiness@gmail.com` là tài
   khoản dùng chung với người thứ hai (memory `tk-claude-chidoanbusiness-dung-chung`), key
   tạo ở đó thì hoá đơn và quyền thu hồi nằm chung với người kia.
3. Nạp secret + nghiệm thu: `python3 /Users/Huy/Claude/App/HuongDienWork/nap-secret-webhook.py`
4. Cấu hình webhook ở `developers.facebook.com/apps/994076413665016` → Messenger → Webhooks,
   subscribe Page với **đủ 3 trường**: `messages` · `messaging_postbacks` · `message_echoes`
   (thiếu `message_echoes` là van an toàn không bao giờ reset — nhân viên trả lời tay mà bộ
   đếm không biết).
5. `CAU_HINH.chinhSachDoiTra` đang là `CHUA_CO` — knowledge base chỉ nói kiểm hàng cùng bưu
   tá. Điền câu chuẩn rồi deploy lại thì bot tự trả lời được; để nguyên thì mọi câu đổi trả
   bị đẩy sang nhân viên (đúng thiết kế, không phải lỗi).
6. ~~Chạy bộ ca vàng + chốt ngưỡng~~ — XONG 01/08/2026. Bộ đã mở rộng **106 → 178 ca** bằng
   câu khách thật; ngưỡng chốt lại trên tập mới (`phan_loai` 0,85 · `chuyen_dung` 0,92),
   dải 06 lượt 87,6-90,4% · 94,4-98,1% · **0 vi phạm CẤM ở cả 06 lượt**.
7. ~~**Quyết hướng cho nhóm câu LIỀU DÙNG / AN TOÀN SỨC KHOẺ**~~ — mã ĐÃ VÁ XONG 01/08/2026
   (nhóm `an_toan` + van `noiLieuDung` + 32 ca vàng sửa đáp án + 08 ca test mới, hai bộ test
   xanh 54/54 và 16/16, 28/28 và 12/12 bản hỏng đều bị bắt; đã deploy, function lên version 6
   và lời gọi verify sai token trả 403 đúng như mong đợi).
8. ⛔ **CÒN NỢ — nạp credit API rồi chạy lại 07 lượt để CHỐT NGƯỠNG.** `NGUONG` đang là `null`
   nên bộ kiểm định thoát mã 2 kèm «NGƯỠNG CHƯA CHỐT»; đó là trạng thái đúng, không phải hỏng.
   Lượt đo 01/08 dừng giữa chừng vì `ANTHROPIC_API_KEY_HDW` **hết số dư** (`credit balance is
   too low`, mã 400) — key vẫn sống, chỉ hết tiền. Đo được 02 lượt trước khi hết: phân loại
   92,7% và 93,8%, chuyển tay 97,2% cả hai, vi phạm CẤM 1 rồi 0. Nạp xong thì chạy:

   ```bash
   set -a; . ~/.config/api-keys.env; set +a; for i in 1 2 3 4 5 6 7; do /opt/homebrew/bin/deno run --allow-read --allow-write --allow-env --allow-net /Users/Huy/Claude/App/HuongDienWork/supabase/kiem-dinh/kiem-dinh-bot.ts --luu /tmp/kd-luot$i.json | grep -E "Phân loại|chuyển tay|Vi phạm"; done
   ```

   Cờ `--luu <file>` (thêm 01/08) đổ TOÀN BỘ kết quả ra đĩa kèm tên van đã kích và câu bị
   chặn — không có nó thì **không đo được chặn oan**, vì bảng in ra chỉ nêu ca không đạt mà
   một van chặn oan vẫn cho ca "đạt" (chuyển tay không bị chấm sai).

   ⚠ **MỘT LƯỢT TỐN KHOẢNG 2 USD, KHÔNG PHẢI 0,5-1 USD.** Huy nạp 5 USD ngày 01/08 và hết
   sạch sau ~2,5 lượt. Con số 0,5-1 USD là tao **ước từ cỡ prompt chứ không đo** — script khi
   đó vứt đi trường `usage` mà API trả sẵn trong mỗi phản hồi. Cỡ thật: system prompt bước trả
   lời **18.906 ký tự (~8.000 token)**, riêng `KB_NGOAI` chiếm **79%**, gửi lại 60 lần mỗi
   lượt; `PROMPT_PHAN_LOAI` 2.991 ký tự gửi 178 lần; cộng nhánh `[NHUONG]` gọi lại **Sonnet**
   với đúng system prompt ấy, Sonnet đắt gấp 3 lần Haiku cả vào lẫn ra.

   Đã vá cùng lượt: (i) script đọc `usage` và in bảng **token vào / ghi cache / đọc cache / ra
   tách theo model, kèm tiền lượt đó và ước 07 lượt** — model lạ thì KÊU chứ không lặng lẽ
   tính giá 0; (ii) **mồi cache** một lời gọi trước khi bung 06 luồng, vì không mồi thì 06 lời
   gọi đầu cùng MISS và cùng trả tiền ghi cache 1,25× cho đúng một nội dung. Mồi phải dùng
   **nguyên văn** system prompt thật — cache khớp theo tiền tố, lệch một ký tự là hỏng mà
   không báo lỗi gì, chỉ hoá đơn biết.

   ⛔ **ĐÍNH CHÍNH 01/08/2026 — NGƯỠNG CACHE TỐI THIỂU CỦA HAIKU 4.5 LÀ 4.096 TOKEN, KHÔNG
   PHẢI 2.048.** Bản ghi trước lấy nhầm con số của **Haiku 3.5**; tra tài liệu chính thức thì
   ngưỡng **không đơn điệu theo đời máy** — Opus 5 / Fable 5 là 512 · Opus 4.8 và Sonnet 5 là
   1.024 · Opus 4.7 và **Haiku 3.5** là 2.048 · Opus 4.6, Opus 4.5 và **Haiku 4.5** là 4.096.
   Suy "đời mới hơn thì ngưỡng thấp hơn" là suy sai, và ở đây nó suýt dẫn tới việc nới prompt
   lên 2.048 token — tốn thêm token vào ở **mọi** lời gọi mà **vẫn không cache được gì**, tức
   vá một khoản phí bằng cách tăng chính khoản phí đó, im lặng.

   Số đo cùng ngày (`deno eval` trên chính hai prompt): `PROMPT_PHAN_LOAI` **2.991 ký tự ≈
   875-1.250 token** — dưới 4.096 rất xa, nên `cache_control` trên nó **chắc chắn không có tác
   dụng** (API không báo lỗi, chỉ trả `cache_creation_input_tokens: 0`). System prompt trả lời
   **18.906 ký tự ≈ 6.800-7.900 token** — trên ngưỡng, nên cache tầng 02 CÓ hiệu lực.

   **Kết luận: KHÔNG nới `PROMPT_PHAN_LOAI`.** Nới cho đủ 4.096 nghĩa là nhồi thêm ~2.850 token,
   gấp hơn 03 lần bản hiện tại, mà nội dung nhồi vào chính là thứ quyết định nhãn ⇒ prompt đổi
   ⇒ **ngưỡng phải chốt lại từ đầu**, đúng vòng luẩn quẩn đang mắc. Khoản tiết kiệm về lý thuyết
   chỉ khoảng 0,14 USD một lượt.

   **Chỗ đáng ngờ hơn, nay ĐÃ CÓ PHÉP ĐO:** cache mặc định sống **05 phút**. Lượt nào chạy lâu
   hơn thế thì cache system prompt trả lời hết hạn giữa chừng, 06 luồng cùng miss và cùng ghi
   lại — bước mồi cache chỉ chặn được lần đầu, không chặn được các lần tái diễn. Bảng token in
   TỔNG ghi cache nên một tổng lớn trông y hệt "prompt dài", không tự khai là "đã ghi lại N
   lần". Nay script lấy `ghi + đọc` của **chính lời gọi mồi** làm cỡ system prompt (con số THẬT
   do API khai, không ước từ ký tự), rồi cuối lượt in thời lượng và `tổng ghi ÷ cỡ = N lần`;
   N > 1,5 thì kêu kèm cách vá (`ttl:"1h"`). Không chốt được cỡ ⇒ KÊU, không lặng lẽ bỏ phép đo.

   ⚠ **Giá Sonnet 5 trong bảng `GIA` đang là 3/15 USD, nhưng có giá giới thiệu 2/10 USD tới
   31/08/2026** — tức phần Sonnet đang bị tính cao hơn thực tế khoảng 1,5 lần. Hoá đơn mới là
   nguồn sự thật; đừng đọc con số bảng in ra thành số tiền đã trả.

### ✅ Hạn cache 1 giờ cho bước trả lời — vá 01/08/2026

**Cơ chế gây tốn:** cache system prompt mặc định sống **05 phút**. Bài thi 178 câu dồn trong
một phút thì hạn đó thừa sức, nên nhìn từ bộ kiểm định không thấy vấn đề gì. Nhưng khách thật
nhắn **rải rác**: đo trên kho chat `App/HuongDien/du-lieu-chat-fb/chat-fb-200-khach-gan-nhat.jsonl`,
tháng 7/2026 có 8.165 tin khách, trung bình 263 tin/ngày (ngày cao nhất 709), bot tự trả khoảng
1/3 — tức khoảng cách giữa hai lượt bot trả lời trong giờ mở cửa vào khoảng 10 phút. Dài hơn
hạn 05 phút, nên **gần như mọi lượt đều phải viết lại cache** cho cùng một system prompt 18.906
ký tự (~7.900 token), thay vì đọc lại bản đã có. Không lỗi, không cảnh báo — chỉ hoá đơn biết.

Ước theo bảng giá Haiku 4.5: **khoảng 40 USD/tháng ở hạn 5 phút, còn 21,6 USD/tháng ở hạn 1
giờ** (tỷ giá 26.168 đ/USD ngày 01/08/2026). Tiền này ra từ **ví API riêng**
`ANTHROPIC_API_KEY_HDW`, không phải gói Claude.

- **Khai bằng `ttl: "1h"` trong `cache_control`. KHÔNG cần beta header** — `ttl` đã là tính
  năng chính thức, đừng đi tìm cờ beta rồi tưởng chưa dùng được.
- **Giá ghi cache hạn 1 giờ là 2× giá vào**, so với 1,25× của hạn 5 phút. Nên nó CHỈ lời khi
  lượt kế tiếp cách lượt trước **quá 5 phút mà chưa quá 1 giờ** — đúng nhịp khách nhắn, SAI
  nếu đem áp cho bài thi dồn dập.
- ⛔ **CHỈ áp cho bước TRẢ LỜI, không áp cho bước phân loại.** `PROMPT_PHAN_LOAI` chỉ ~875-1.250
  token, dưới ngưỡng cache tối thiểu 4.096 của Haiku 4.5 — cache ở đó không có tác dụng dù
  khai gì (API không báo lỗi, chỉ trả `cache_creation_input_tokens: 0`), nên trả giá ghi 2×
  cho nó là lỗ thuần. Ca 92 của `test-webhook.ts` canh đúng chiều nới tay này.
- **Sonnet là cache RIÊNG** — cache khoá theo model, nên nhánh `[NHUONG]` phải khai hạn riêng.
  Bỏ sót một nhánh thì nhánh đó vẫn đốt tiền y như cũ. Ca 91 đếm đúng 02 lời gọi.
- ⚠ **KHÔNG nới `PROMPT_PHAN_LOAI` cho đủ 4.096 token để cache được.** Đo lại trên khách thật:
  nới chỉ rẻ khi chạy bài thi 178 câu dồn trong 01 phút; với khách nhắn rải rác thì nó ĐẮT
  HƠN, vì cứ 5 phút cache hết hạn là phải ghi lại một prompt dài hơn. Cộng thêm: nội dung nhồi
  vào chính là thứ quyết định nhãn ⇒ prompt đổi ⇒ **ngưỡng phải chốt lại từ đầu**.

### ✅ Sổ token chung trên đĩa — vá 01/08/2026

**Cơ chế gây vấp:** bảng token in ra cuối mỗi lượt kiểm định chỉ nói về **lượt đang chạy**, và
biến mất cùng cửa sổ terminal. Nguyên nhân gốc của vụ cháy 5 USD ngày 01/08 không phải một lượt
quá đắt, mà là **ba phiên Claude chạy song song cùng đốt một khoá mà không phiên nào biết phiên
kia đã chạy bao nhiêu lượt** — đo lại từ transcript: 17,6 lượt trong 02 ngày, khoảng 3.100 câu
gửi lên, bằng lượng khách nhắn thật của 12 ngày.

- Cuối mỗi lượt chạy thật, `kiem-dinh-bot.ts` ghi NỐI một dòng mỗi model vào
  `~/Claude/HeThong/so-token-api.jsonl` (quyền 600 — mỗi dòng mang số tiền thật, mục 18 lớp 6).
- Cộng dồn: `python3 /Users/Huy/Claude/HeThong/so-token-api.py` (cờ `--ngay N`, `--json`).
  Ngưỡng cảnh báo **5,0 USD/ngày** — đúng bằng lần nạp thẻ đã cháy hôm 01/08. Đổi ngưỡng thì
  sửa cả hằng số `NGUONG_USD_NGAY` lẫn con số ở đây trong CÙNG một lượt.
- **Bên ghi là `HeThong/so_token_api.ts`, GỌI hàm chung — cấm chép.** Hai nơi cùng ghi một sổ
  mà mỗi nơi một khuôn dòng thì phép cộng lặng lẽ sai, và đây là hai ngôn ngữ khác nhau nên
  không trình biên dịch nào bắt được lệch khoá. Ca 13 của bộ test đọc thẳng khai báo kiểu
  `DongSo` trong file TS rồi đối chiếu.
- ⚠ **Lượt chạy thật nay cần `--allow-write`.** Thiếu quyền thì lượt vẫn chạy nhưng tiền của
  nó không vào tổng — hàm ghi kêu ra stderr, cố ý không im.
- ⚠ **Đừng trộn với `HeThong/lich-su-token.jsonl`** — file kia đo token của phiên Claude Code,
  tiêu từ gói thuê bao. Lẫn hai ví là lẫn cả mức độ lo.
- Bộ test `HeThong/test-so-token-api.py`: **13 ca · 12 bản hỏng**, đã nạp `khoe.py`.
  ⚠ Bài học khi dựng, đừng lặp: 02 ca đầu tiên dựng dữ liệu thử bằng `NGUONG_USD_NGAY ± ε` —
  **ca neo động theo hằng số**, nên bản hỏng nới ngưỡng lên 999999 làm dữ liệu trôi theo và ca
  VẪN XANH trong khi cảnh báo đã chết hẳn. Phải ghim CỨNG con số ở ít nhất một ca mỗi chiều.
  Và một bản hỏng gỡ thẳng phép so trong thân ca canh khuôn (ca 13) cũng không bắt được — **ca
  test không tự canh được chính mình**; phải tráo từ bên ngoài (hằng số `DUONG_TS`).

### ✅ Lỗi gọi model tách khỏi vi phạm CẤM — vá 01/08/2026

**Cơ chế gây vấp:** nhánh `catch` của vòng chạy thật xếp `LỖI GỌI MODEL` vào `vi_pham`, cùng
cột với "bịa giá / markdown gửi khách". Đúng ý định fail-closed, nhưng **sai tên gọi**: lượt
01/08 hết số dư API in ra `Vi phạm CẤM: 178 (ngưỡng cứng 0)` kèm lý do *"178 vi phạm CẤM (bịa
giá / markdown gửi khách / lộ dữ kiện cấm)"* — tức bảng khai bot bịa giá 178 lần trong một
lượt **bot chưa hề chạy**, và hai tỉ lệ in 0,0% trông y hệt thoái hoá toàn diện. Ba dòng ✗ mỗi
ca cũng khai sai hành vi (*"PHẢI chuyển nhân viên mà bot tự trả lời"* cho ca không có câu trả
lời nào). Vá lần trước là **một đoạn cảnh báo trong file này** — cảnh báo bằng tài liệu không
phải cổng, người đọc bảng vẫn đọc con số sai; đúng lớp lỗi mục 17 CLAUDE.md gốc.

- Cột riêng `Cham.loi_goi` (tuỳ chọn, chỉ nhánh `catch` đặt) + `TongHop.so_loi_goi`. **Vẫn
  fail-closed y như cũ** — `dat = false`, mã thoát ≠ 0; chỉ đổi tên và tách cột.
- Dòng lý do đặt **ĐẦU mảng `ly_do`**, trước mọi nhánh so ngưỡng, và bảng in cảnh báo **NGAY
  TRÊN** hai dòng tỉ lệ: người đọc dừng ở dòng đầu tiên họ hiểu, để cuối bảng là quá muộn.
- Ca có `loi_goi` thì phần "Ca KHÔNG đạt" **chỉ in nguyên nhân thật**, bỏ hai dòng hệ quả giả.
- Bộ test: ca 11 viết lại thành 04 vế tách rời (vẫn KHÔNG ĐẠT · `so_loi_goi` đúng ·
  `so_vi_pham` = 0 · lý do nói "CHƯA ĐO ĐƯỢC") — gộp thành một cờ thì bản hỏng nào cũng làm ca
  đỏ và ca mất khả năng chỉ ra hỏng ở đâu. Thêm **02 bản hỏng canh hai chiều**: gỡ nhánh
  `so_loi_goi > 0` (fail-open, hết tiền mà bảng im) và **nhập lại `loi_goi` vào `so_vi_pham`**
  (khôi phục nguyên bug cũ khi ai đó "gộp cho gọn"). Nghiệm thu 01/08: **16/16 ca · 14/14 bản
  hỏng đều bị bắt**.

### ⚠ ĐỔI GIỌNG BOT: sửa chữ thì rẻ, nhưng PHẢI dạy lại van hứa-hẹn rồi chạy kiểm

Giọng nằm ở `GIONG_VAN` (`faq.ts:131`, ~640 ký tự ≈ 3% system prompt bước trả lời). Sửa rồi
deploy là xong — **không có bước training nào**, và chi phí token gần như không đổi (chỉ tốn
một lần ghi lại bộ nhớ đệm, cỡ vài xu).

⛔ **Chỗ tốn thật nằm ở van, không nằm ở prompt.** `huaCoNguoiTraLoi()` (`xac-minh.ts`) nhận
diện lời hứa qua **cụm từ cố định** — *"sẽ báo"*, *"sẽ tư vấn"*, *"để nhân viên"*, *"sẽ vào"*.
Giọng mới nói khác đi (*"em check rồi rep mẹ liền nha"*) là van trượt ⇒ bot hứa với khách rồi
bỏ mặc, đúng lỗi số 1 mà bộ ca vàng bắt được. Nên mọi lần đổi giọng phải: (i) rà lại bảng cụm
của `huaCoNguoiTraLoi` và `noiLieuDung` theo lối nói MỚI; (ii) chạy ít nhất **01 lượt bộ ca
vàng (~2 USD)** rồi đọc `--luu` xem van kích bao nhiêu lần.

Ngược lại, `PROMPT_PHAN_LOAI` **không đụng tới** khi đổi giọng — ngưỡng phân loại giữ nguyên,
không phải chốt lại.

### ✅ Giọng bot chốt lại theo SỐ ĐO người thật — đổi 01/08/2026

Huy hỏi "giọng nào hợp mẹ bỉm 25-35". Thay vì đoán, đo kho chat thật
`App/HuongDien/du-lieu-chat-fb/chat-fb-200-khach-gan-nhat.jsonl`: gộp các tin nhân viên liên
tiếp thành MỘT lượt (không gộp thì "vâng"/"dạ" đếm thành lượt riêng và độ dài bị kéo xuống
giả), bỏ lượt dưới 40 ký tự ⇒ **32.742 lượt thực chất**.

| Nét | Người thật | Bot bản cũ |
|---|---|---|
| gọi khách | **"chị" 36,3%** · "mẹ" **1,2%** | "mẹ" ở mọi câu ⇒ **NGƯỢC HẲN, chênh 31 lần** |
| độ dài | trung vị **103 ký tự · 02 câu** | cho phép 3–4 câu |
| lễ phép | "ạ" **79,0%** · mở "Dạ" **16,8%** | — |
| tiểu từ | "nhé" **30,0%** · "nha" **3,8%** | không quy định |
| emoji | **84,1% lượt KHÔNG có** emoji nào | "0–1 mỗi tin" (đã đúng) |

**Kết luận đo được: giọng hợp KHÔNG phải GenZ mà là nhân viên bán hàng lễ phép, trả lời cực
ngắn, xưng em–chị.** Mẫu GenZ trình trước đó dùng "nha" — lệch ngay với số đo. Huy chốt qua
bảng chọn: **đổi sang "chị" + siết còn 02 câu**. Đã deploy, function **version 8**, verify sai
token trả 403.

⚠ **PHÂN ĐỊNH BẮT BUỘC KHI ĐỔI XƯNG HÔ — 10 chỗ đổi, 05 chỗ CỐ Ý GIỮ:**
- **Đổi**: mọi chỗ xưng hô với khách ở bước TRẢ LỜI — `GIONG_VAN`, `CAM`,
  `TU_VAN_THEO_GIAI_DOAN`, nhánh ngoài giờ, `dungSystemPromptDayDu`, và **`cauGiuCho()`**
  (câu bot gửi khi chuyển nhân viên — bỏ sót chỗ này là khách thấy hai xưng hô trong một
  cuộc).
- **GIỮ**: `"cửa hàng mẹ và bé"` (tên loại hình, 02 chỗ) và **03 chỗ trong `PROMPT_PHAN_LOAI`**
  (`"mẹ đang cho con bú"`, `"mẹ hỏi cho uống gì"` — mô tả ĐỐI TƯỢNG, không phải xưng hô).
  Đụng vào `PROMPT_PHAN_LOAI` là **phải chốt lại ngưỡng từ đầu**, mà ngưỡng đang chưa chốt.

**Van KHÔNG neo xưng hô nên không phải vá** — đã kiểm: `xac-minh.ts` chỉ có chữ "mẹ" trong
chú thích, bộ ca vàng có **0** mẫu `cam`/`can` neo xưng hô. Luật cũ *"CẤM neo van vào xưng
hô"* (dựng 01/08 sau khi model xưng "chị" làm van trượt) chính là thứ cứu đợt đổi này, và
`test-webhook.ts` có sẵn bản hỏng canh đúng chiều đó. Nghiệm thu: **57/57 ca · 29/29 bản
hỏng**.

⛔ **CÒN NỢ: chạy 01 lượt bộ ca vàng (~2 USD) sau khi có credit.** Bộ test xác định không đo
được chiều này — van hứa-hẹn khớp theo CỤM TỪ, mà giọng mới có thể sinh ra lối hứa chưa nằm
trong bảng. Đọc `--luu` xem van `hua` kích bao nhiêu lần so với mốc cũ (**8 rồi 6 lần** trên
02 lượt của giọng cũ); tụt hẳn về 0 là dấu hiệu van trượt, không phải bot ngoan hơn.

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit): bigfile-nav, data-backup, deploy-static, doc-single-file-app, local-store, lock-static-app, pwa-healthcheck, scaffold-vibe-pwa, supabase-sync, theme-pack, web-push.
