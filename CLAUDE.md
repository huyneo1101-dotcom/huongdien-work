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
| `functions/messenger-webhook/test-webhook.ts` | cổng XÁC ĐỊNH: chữ ký `X-Hub-Signature-256`, giờ làm việc, van an toàn, van hứa-hẹn, bộ lọc markdown, nhánh quyết định | `deno run --allow-read --allow-write --allow-run <file> --tu-kiem` — 41 ca · 22 bản hỏng |
| `kiem-dinh/test-kiem-dinh-bot.ts` | phần CHẤM của bộ ca vàng 106 câu | `deno run --allow-read --allow-write --allow-run --allow-env --allow-net <file>` — 16 ca · 12 bản hỏng |

Cả hai đã nạp `BO_TEST` của `khoe.py`.

**Bộ ca vàng `kiem-dinh/bo-ca-vang-messenger.json` — 106 câu khách thật**, đáp án gán tay
(mục 17 CLAUDE.md gốc, họ "bộ ca vàng": công cụ có đầu ra là PHÁN XÉT thì ca tự bịa là chưa
test). Chạy thật cần `ANTHROPIC_API_KEY_HDW`:

```bash
set -a; . ~/.config/api-keys.env; set +a; /opt/homebrew/bin/deno run --allow-read --allow-env --allow-net /Users/Huy/Claude/App/HuongDienWork/supabase/kiem-dinh/kiem-dinh-bot.ts
```

**NGƯỠNG ĐÃ CHỐT 01/08/2026** (sửa ở đây thì sửa cả `NGUONG` trong mã, cùng lượt):
`phan_loai = 0,90` · `chuyen_dung = 0,92` · vi phạm CẤM ngưỡng cứng **0** · thiếu dữ kiện
mong đợi trần **3**. Kết quả nghiệm thu: **93,4% phân loại · 98,0% chuyển tay · 0 vi phạm** ⇒ ĐẠT.

⚠ **Ngưỡng lấy theo giá trị THẤP NHẤT qua nhiều lượt, không lấy theo lượt đẹp nhất.** Model
không tất định: 04 lượt trên cùng một bản mã nguồn cho phân loại 92,5-94,3% và chuyển tay
94,0-98,0%. Chốt sát lượt đẹp là dựng cổng đỏ oan ngay lượt sau.

⚠ **Chiều KÊU-NÂNG-NGƯỠNG phải có biên RỘNG HƠN dao động** (`BIEN_NANG` = 0,06 và 0,08). Luật
"cao hơn ngưỡng cũng phải trượt" viết cho công cụ tất định; bê nguyên sang đây với biên 0,02
thì lượt nào cũng kêu nâng — vẫn là cổng chập chờn, chỉ đổi chiều. Đã vấp thật khi chốt.

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

### 07 ca còn trượt — đã soi, cố ý để nguyên

Ba câu tư vấn chung ("tã quần khác bỉm dán thế nào", "sữa nào tăng cân", "bé lười uống sữa")
rơi `khong_chac` do luật *phân vân faq_tinh/khong_chac thì chọn khong_chac* — an toàn nhưng
đẩy việc sang nhân viên. Hai câu chưa có dữ kiện (ship quốc tế, TikTok) bot tự trả lời kèm
hotline thay vì chuyển. Nới luật để vá mấy ca này sẽ kéo theo rủi ro ở nhóm nhạy cảm, nên giữ
nguyên và để ngưỡng phản ánh.

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

1. `FB_APP_SECRET` · `FB_PAGE_ACCESS_TOKEN` · `FB_WEBHOOK_VERIFY_TOKEN` — chạy
   `python3 /Users/Huy/Claude/App/HuongDienWork/cam-facebook-key-hdw.py`
2. `ANTHROPIC_API_KEY_HDW` — chạy `python3 /Users/Huy/Claude/App/HuongDienWork/cam-anthropic-key-hdw.py`
3. Nạp secret + nghiệm thu: `python3 /Users/Huy/Claude/App/HuongDienWork/nap-secret-webhook.py`
4. Cấu hình webhook ở `developers.facebook.com/apps/994076413665016` → Messenger → Webhooks,
   subscribe Page với **đủ 3 trường**: `messages` · `messaging_postbacks` · `message_echoes`
   (thiếu `message_echoes` là van an toàn không bao giờ reset — nhân viên trả lời tay mà bộ
   đếm không biết).
5. `CAU_HINH.chinhSachDoiTra` đang là `CHUA_CO` — knowledge base chỉ nói kiểm hàng cùng bưu
   tá. Điền câu chuẩn rồi deploy lại thì bot tự trả lời được; để nguyên thì mọi câu đổi trả
   bị đẩy sang nhân viên (đúng thiết kế, không phải lỗi).
6. ~~Chạy bộ ca vàng + chốt ngưỡng~~ — XONG 01/08/2026, ĐẠT (93,4% · 98,0% · 0 vi phạm).

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit): bigfile-nav, data-backup, deploy-static, doc-single-file-app, local-store, lock-static-app, pwa-healthcheck, scaffold-vibe-pwa, supabase-sync, theme-pack, web-push.
