#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cắm Facebook App ID/Secret + Page Access Token + Webhook Verify Token
riêng cho chatbot Messenger Hương Diện Baby Mart.

Chạy:  python3 /Users/Huy/Claude/App/HuongDienWork/cam-facebook-key-hdw.py

Lấy các giá trị này ở developers.facebook.com/apps (xem hướng dẫn từng bước
Zim đã đưa: tạo App loại Business → thêm sản phẩm Messenger → kết nối
fanpage Hương Diện Baby Mart → Generate Token → App Settings/Basic để lấy
App Secret). Webhook Verify Token là chuỗi mày TỰ ĐẶT, không phải Facebook cấp.

Việc script làm (theo đúng mẫu cam-anthropic-key-hdw.py — mục 14c CLAUDE.md,
không hỏi secret qua chat):
  1. Hỏi 4 giá trị bằng getpass (không hiện lên màn hình, không vào lịch sử shell).
  2. Gọi thử Graph API: xác nhận App ID/Secret là 1 cặp đúng (lấy App Access
     Token qua client_credentials), và Page Access Token còn sống (gọi /me,
     in TÊN Page trả về để tự kiểm, không in token).
  3. Sao lưu file cũ, ghi/thay 4 dòng khoá, đặt quyền 600.
"""

import getpass
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

FILE_ENV = Path.home() / ".config" / "api-keys.env"
GRAPH = "https://graph.facebook.com/v19.0"

KHOA_APP_ID = "FB_APP_ID_HDW"
KHOA_APP_SECRET = "FB_APP_SECRET_HDW"
KHOA_PAGE_TOKEN = "FB_PAGE_ACCESS_TOKEN_HDW"
KHOA_VERIFY = "FB_WEBHOOK_VERIFY_TOKEN_HDW"


def goi_curl(url, tham_so=None):
    """GET Graph API qua curl (đọc keychain macOS, tránh lỗi cert như các script khác)."""
    if tham_so:
        qs = "&".join(f"{k}={v}" for k, v in tham_so.items())
        url = f"{url}?{qs}"
    try:
        r = subprocess.run(
            ["curl", "-s", url, "--max-time", "30"],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None, "gọi Facebook quá 60 giây không trả lời"
    if r.returncode != 0:
        return None, f"curl thoát mã {r.returncode}: {r.stderr.strip()[:200]}"
    try:
        return json.loads(r.stdout), None
    except json.JSONDecodeError:
        return None, f"Facebook trả về thứ không phải JSON: {r.stdout[:200]}"


def thu_app_id_secret(app_id, app_secret):
    """Xác nhận App ID/Secret là 1 cặp đúng qua client_credentials."""
    d, loi = goi_curl(f"{GRAPH}/oauth/access_token", {
        "client_id": app_id, "client_secret": app_secret, "grant_type": "client_credentials",
    })
    if loi:
        return False, loi
    if d and d.get("access_token"):
        return True, "App ID/Secret khớp nhau"
    mo_ta = (d or {}).get("error", {}).get("message", json.dumps(d, ensure_ascii=False)[:300])
    return False, f"Facebook từ chối: {mo_ta}"


def thu_page_token(page_token):
    """Xác nhận Page Access Token còn sống, trả về TÊN page (không phải token)."""
    d, loi = goi_curl(f"{GRAPH}/me", {"fields": "name,id", "access_token": page_token})
    if loi:
        return False, loi
    if d and d.get("name"):
        return True, f"token sống — gắn với Page \"{d['name']}\" (id {d.get('id')})"
    mo_ta = (d or {}).get("error", {}).get("message", json.dumps(d, ensure_ascii=False)[:300])
    return False, f"Facebook từ chối: {mo_ta}"


def doc_env():
    if not FILE_ENV.exists():
        return []
    return FILE_ENV.read_text(encoding="utf-8").splitlines()


def ghi_env(dong_cu, gia_tri: dict):
    """gia_tri: {KHOA: giá trị}. Thay dòng đã có, thêm dòng mới cho khoá chưa có."""
    ra = list(dong_cu)
    da_thay = set()
    for i, dong in enumerate(ra):
        for khoa in gia_tri:
            if re.match(rf"^\s*#?\s*{re.escape(khoa)}\s*=", dong):
                ra[i] = f"{khoa}={gia_tri[khoa]}"
                da_thay.add(khoa)
    con_thieu = [k for k in gia_tri if k not in da_thay]
    if con_thieu:
        ra.append("")
        ra.append("# --- Facebook Messenger: chatbot Hương Diện (App ID/Secret + Page Token + Webhook Verify) ---")
        for k in con_thieu:
            ra.append(f"{k}={gia_tri[k]}")
    return ra


def hoi(nhan, bat_buoc_tien_to=None):
    while True:
        gt = getpass.getpass(f"{nhan} (gõ vào, màn hình sẽ KHÔNG hiện) → ").strip()
        if not gt:
            print("✗ Trống, gõ lại.", file=sys.stderr)
            continue
        return gt


def main():
    print(__doc__.split("Việc script làm")[0])
    print("=" * 70)

    da_co = doc_env()
    khoa_da_co = [k for k in (KHOA_APP_ID, KHOA_APP_SECRET, KHOA_PAGE_TOKEN, KHOA_VERIFY)
                  if any(re.match(rf"^\s*{re.escape(k)}\s*=\s*\S", d) for d in da_co)]
    if khoa_da_co:
        print(f"Đã có sẵn: {', '.join(khoa_da_co)}")
        if input("Ghi đè hết cả 4 khoá? (g/K) ").strip().lower() != "g":
            return 0

    app_id = hoi("Facebook App ID (App Settings → Basic)")
    app_secret = hoi("Facebook App Secret (App Settings → Basic → Show)")
    print("\nĐang kiểm App ID/Secret…")
    duoc, mo_ta = thu_app_id_secret(app_id, app_secret)
    if not duoc:
        print(f"✗ App ID/Secret KHÔNG khớp: {mo_ta}", file=sys.stderr)
        print("  Chưa ghi gì vào file. Kiểm lại rồi chạy lại.", file=sys.stderr)
        return 1
    print(f"✓ {mo_ta}")

    page_token = hoi("Page Access Token (Messenger → Access Tokens → Generate Token)")
    print("\nĐang kiểm Page Access Token…")
    duoc, mo_ta = thu_page_token(page_token)
    if not duoc:
        print(f"✗ Page Access Token KHÔNG dùng được: {mo_ta}", file=sys.stderr)
        print("  Chưa ghi gì vào file. Kiểm lại rồi chạy lại.", file=sys.stderr)
        return 1
    print(f"✓ {mo_ta}")

    verify_token = hoi("Webhook Verify Token (chuỗi mày TỰ ĐẶT, không phải Facebook cấp)")

    dong = doc_env()
    if FILE_ENV.exists():
        sao_luu = FILE_ENV.with_suffix(".env.bak")
        shutil.copy2(FILE_ENV, sao_luu)
        os.chmod(sao_luu, 0o600)
        print(f"✓ Đã sao lưu bản cũ: {sao_luu}")

    FILE_ENV.parent.mkdir(parents=True, exist_ok=True)
    gia_tri = {
        KHOA_APP_ID: app_id,
        KHOA_APP_SECRET: app_secret,
        KHOA_PAGE_TOKEN: page_token,
        KHOA_VERIFY: verify_token,
    }
    FILE_ENV.write_text("\n".join(ghi_env(dong, gia_tri)) + "\n", encoding="utf-8")
    os.chmod(FILE_ENV, 0o600)
    print(f"✓ Đã ghi {FILE_ENV} (quyền 600), 4 khoá: {', '.join(gia_tri)}")
    print("\nXong phần App ID/Secret + Page Token + Verify Token.")
    print("Còn thiếu để hoàn tất checklist Facebook: cấu hình URL Webhook trên")
    print("developers.facebook.com — CHỈ làm được sau khi Edge Function đã deploy")
    print("(Facebook cần gọi thử URL đó để xác minh lúc mày bấm Verify and Save).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
