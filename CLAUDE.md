# Hương Diện · Quản lý công việc — app quản lý công việc & kinh doanh cho chủ shop mẹ&bé (Kanban, Pomodoro, lịch, chỉ số tuần, kho kiến thức, playbook, thói quen)

App tĩnh một-file: toàn bộ UI + logic + CSS trong `index.html` (~2.895 dòng, ~224KB), React 18 + Babel Standalone qua CDN, KHÔNG build step. Deploy tĩnh (chưa có CI/CD — chỉ serve tĩnh `index.html`).

## Quy tắc làm việc với file này
- **KHÔNG đọc cả `index.html` (~224KB)** — dùng grep định vị rồi Read cửa sổ nhỏ (xem skill `bigfile-nav`).
- ⚠️ **Thiếu `sw.js` và `manifest.json`**: `index.html` gọi `serviceWorker.register('sw.js')` nhưng repo KHÔNG có `sw.js` và cũng KHÔNG có manifest → PWA/offline hỏng, register luôn lỗi. Cần bổ sung hoặc gỡ dòng register (xem skill `pwa-healthcheck`).
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
| `hdw.dark` / `hdw.zen` / `hdw.inboxSeen` | Cờ giao diện tối / zen / đã xem | scalar |

- Khoá riêng của sync (KHÔNG nằm trong blob): `hdw.synccode`, `hdw.synclast`.
- **Đồng bộ nhiều máy: mã sync** (`Sync` dòng ~263) — push/pull toàn bộ blob các khoá `hdw.*` qua Supabase Edge Function `hdw-sync`, KHÔNG cần đăng nhập; nhập cùng "mã sync" trên máy khác để dùng chung dữ liệu (pattern C trong skill `supabase-sync`). Đổi cấu trúc dữ liệu: skill `local-store` (hiện chưa có SCHEMA_VERSION/migration).

## Bản đồ component chính
- `App` — dòng ~646; state `view` chọn màn hình. Các tab/màn hình:
  - `dash` → `Dash` (tổng quan), `board` → `Board` (Kanban), `proj` → `Projects`
  - `cal` → `Calendar` (lịch), `daily` → `Daily` (thói quen), `today` → `Today` (kế hoạch + 3 wins)
  - `stats` → `Stats` (chỉ số tuần), `brain` → `BrainEnergy` (năng lượng não)
  - `sales` → `Sales` + `kd` → `BizBook` (kinh doanh/playbook), `book` → `Notebook`, `learn` → `Knowledge`
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
