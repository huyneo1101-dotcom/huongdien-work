#!/bin/sh
# Đưa Hương Diện Work lên Cloudflare Pages (https, miễn phí, mã nguồn KHÔNG công khai).
# Trước 31/07/2026 app chạy trên GitHub Pages, và Pages miễn phí buộc repo phải PUBLIC —
# tức toàn bộ mã nguồn, tên bảng Supabase và mẫu mã đồng bộ nằm ngoài internet. Cloudflare
# Pages không đòi repo công khai, nên chuyển sang đây rồi khoá repo lại.
#
# Chỉ đẩy 4 file giao diện — KHÔNG đẩy CLAUDE.md, tài liệu thiết kế, script cắm khoá.
set -e

GOC=/Users/Huy/Claude/App/HuongDienWork
WEB=$GOC/.web

wrangler whoami >/dev/null 2>&1 || wrangler login

rm -rf "$WEB"
mkdir -p "$WEB"
cp "$GOC/index.html" "$GOC/manifest.json" "$GOC/sw.js" "$GOC/icon.svg" "$WEB/"

# ⚠ PHẢI là --branch=production. Nhánh khác (kể cả "main") vào hàng PREVIEW, và khi ấy
# địa chỉ chính trả 404 trong khi lệnh deploy vẫn báo thành công — hỏng câm, đã vấp thật
# ở Sổ Công Nợ ngày 31/07/2026 (02 lượt đẩy đều rơi vào Preview).
wrangler pages deploy "$WEB" --project-name=huongdien-work --branch=production --commit-dirty=true

rm -rf "$WEB"
# wrangler sinh wrangler.toml ở thư mục đang đứng; để lại thì mọi lệnh wrangler sau đó
# trong thư mục ấy đọc nhầm cấu hình.
rm -f "$GOC/wrangler.toml"

echo
echo "Nghiệm thu bằng chính địa chỉ sẽ đưa cho người dùng, không đọc dòng 'Deployment complete':"
echo "  curl -s -o /dev/null -w '%{http_code}\\n' https://huongdien-work.pages.dev/"
