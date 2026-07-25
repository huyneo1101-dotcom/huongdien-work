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
- Chưa có `.github/workflows/`, `netlify.toml`. Repo chỉ gồm `index.html` + `README.md` → serve tĩnh thủ công. Muốn nối CI/CD: skill `deploy-static`.

## Skills dùng chung
Repo có `.claude/skills/` (11 skill từ plugin vibe-pwa-kit): bigfile-nav, data-backup, deploy-static, doc-single-file-app, local-store, lock-static-app, pwa-healthcheck, scaffold-vibe-pwa, supabase-sync, theme-pack, web-push.
