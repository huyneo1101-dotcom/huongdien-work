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
| `functions/messenger-webhook/test-webhook.ts` | cổng XÁC ĐỊNH: chữ ký `X-Hub-Signature-256`, giờ làm việc, van an toàn, nhánh quyết định, cổng chống bịa số liệu | `deno run --allow-read --allow-write --allow-run <file> --tu-kiem` — 28 ca · 14 bản hỏng |
| `kiem-dinh/test-kiem-dinh-bot.ts` | phần CHẤM của bộ ca vàng 106 câu | `deno run --allow-read --allow-write --allow-run --allow-env --allow-net <file>` — 12 ca · 8 bản hỏng |

Cả hai đã nạp `BO_TEST` của `khoe.py`.

**Bộ ca vàng `kiem-dinh/bo-ca-vang-messenger.json` — 106 câu khách thật**, đáp án gán tay
(mục 17 CLAUDE.md gốc, họ "bộ ca vàng": công cụ có đầu ra là PHÁN XÉT thì ca tự bịa là chưa
test). Chạy thật cần `ANTHROPIC_API_KEY_HDW`:

```bash
set -a; . ~/.config/api-keys.env; set +a; /opt/homebrew/bin/deno run --allow-read --allow-env --allow-net /Users/Huy/Claude/App/HuongDienWork/supabase/kiem-dinh/kiem-dinh-bot.ts
```

⛔ **NGƯỠNG TRONG `kiem-dinh-bot.ts` ĐANG LÀ `null` — CHƯA CHỐT.** Cố ý: ngưỡng phải lấy từ
số đo, không đặt theo mong muốn. Chạy `--chot-nguong` để lấy gợi ý, rồi sửa CẢ `NGUONG` trong
mã LẪN con số ghi ở đây trong cùng lượt. Chừng nào còn `null` thì bộ này luôn báo KHÔNG ĐẠT —
đó là fail về phía KÊU, không phải lỗi.

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
6. Chạy bộ ca vàng + chốt ngưỡng.

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit): bigfile-nav, data-backup, deploy-static, doc-single-file-app, local-store, lock-static-app, pwa-healthcheck, scaffold-vibe-pwa, supabase-sync, theme-pack, web-push.
