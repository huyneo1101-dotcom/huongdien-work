#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Đổi USER token (copy từ Graph API Explorer) sang PAGE token VĨNH VIỄN.

    python3 /Users/Huy/Claude/App/HuongDienWork/doi-user-token-sang-page-vinh-vien.py

Chuỗi việc: clipboard → user token dài hạn (60 ngày) → page token (không hết hạn).
Cần `FB_APP_SECRET_HDW` đã có trong `~/.config/api-keys.env`.

Vì sao page token lấy qua bước này thì KHÔNG hết hạn: Facebook cấp page token
không hạn khi nó được xin bằng một user token DÀI HẠN. Xin bằng user token ngắn
hạn thì page token thừa hưởng đúng hạn ngắn đó — nhìn bề ngoài y hệt, chỉ khác ở
`expires_at`, nên phải nghiệm thu bằng `debug_token` chứ đừng tin là xong.

Token đi thẳng clipboard → file, KHÔNG qua khung chat, KHÔNG in ra màn hình
(mục 14c CLAUDE.md). Chỉ in độ dài và thứ Facebook trả về.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

FILE_ENV = Path.home() / ".config" / "api-keys.env"
GRAPH = "https://graph.facebook.com/v19.0"
APP_ID = "994076413665016"
PAGE_ID = "751373258220832"
KHOA_TOKEN = "FB_PAGE_ACCESS_TOKEN_HDW"
KHOA_SECRET = "FB_APP_SECRET_HDW"


def goi(path, tham_so):
    qs = "&".join("%s=%s" % (k, v) for k, v in tham_so.items())
    r = subprocess.run(["curl", "-s", "%s%s?%s" % (GRAPH, path, qs), "--max-time", "30"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None, "curl thoát mã %d" % r.returncode
    try:
        return json.loads(r.stdout), None
    except json.JSONDecodeError:
        return None, "Facebook trả về thứ không phải JSON: %s" % r.stdout[:200]


def doc_khoa(ten):
    if not FILE_ENV.exists():
        return None
    for d in FILE_ENV.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*%s\s*=\s*(.+)$" % re.escape(ten), d)
        if m:
            return m.group(1).strip()
    return None


def doc_clipboard():
    r = subprocess.run(["pbpaste"], capture_output=True, text=True)
    if r.returncode != 0:
        return None, "không đọc được clipboard (pbpaste thoát mã %d)" % r.returncode
    v = r.stdout.strip()
    if not v:
        return None, "clipboard rỗng"
    if not v.startswith("EAA") or len(v) < 100:
        return None, "clipboard không phải access token (dài %d, tiền tố %r)" % (len(v), v[:3])
    return v, None


def cho_clipboard(tran_giay=180, nhip=2):
    """Chờ token xuất hiện trong clipboard — xem lý do ở cam-app-secret-tu-clipboard.py:
    thao tác copy dòng lệnh để chạy script này sẽ ghi đè mất thứ script cần đọc."""
    v, loi = doc_clipboard()
    if not loi:
        return v, None
    print("Clipboard chưa có access token (%s)." % loi)
    print("→ Sang Chrome bấm nút copy ở ô 'Mã truy cập'. Script tự nhận, chờ tối đa %ds…"
          % tran_giay)
    da = 0
    while da < tran_giay:
        time.sleep(nhip)
        da += nhip
        v, loi = doc_clipboard()
        if not loi:
            print("✓ Nhận được token sau %d giây." % da)
            return v, None
    return None, "hết %d giây chờ mà clipboard vẫn chưa có access token" % tran_giay


def mo_ta(tok):
    d, loi = goi("/debug_token", {"input_token": tok, "access_token": tok})
    if loi:
        return None, loi
    d = (d or {}).get("data", {})
    if not d.get("is_valid"):
        return None, "token không hợp lệ: %s" % str(d.get("error", d))[:200]
    han = "KHÔNG hết hạn" if d.get("expires_at") == 0 else "hết hạn lúc %s" % d.get("expires_at")
    return d, "type=%s, id %s, %s, quyền: %s" % (
        d.get("type"), d.get("profile_id") or d.get("user_id"), han,
        ", ".join(d.get("scopes", [])))


def ghi(token):
    dong = FILE_ENV.read_text(encoding="utf-8").splitlines() if FILE_ENV.exists() else []
    sl = FILE_ENV.with_suffix(".env.bak")
    shutil.copy2(FILE_ENV, sl)
    os.chmod(sl, 0o600)
    thay = False
    for i, d in enumerate(dong):
        if re.match(r"^\s*#?\s*%s\s*=" % re.escape(KHOA_TOKEN), d):
            dong[i] = "%s=%s" % (KHOA_TOKEN, token)
            thay = True
    if not thay:
        dong += ["", "%s=%s" % (KHOA_TOKEN, token)]
    FILE_ENV.write_text("\n".join(dong) + "\n", encoding="utf-8")
    os.chmod(FILE_ENV, 0o600)
    print("✓ Đã ghi %s vào %s (quyền 600)" % (KHOA_TOKEN, FILE_ENV))


def main():
    secret = doc_khoa(KHOA_SECRET)
    if not secret:
        print("✗ Chưa có %s — chạy cam-app-secret-tu-clipboard.py trước." % KHOA_SECRET,
              file=sys.stderr)
        return 1

    tok_user, loi = cho_clipboard()
    if loi:
        print("✗ %s" % loi, file=sys.stderr)
        return 1

    d, m = mo_ta(tok_user)
    if not d:
        print("✗ Token trong clipboard không dùng được: %s" % m, file=sys.stderr)
        return 1
    print("Token clipboard: %s" % m)

    print("\nB1. Đổi sang user token dài hạn…")
    r, loi = goi("/oauth/access_token", {
        "grant_type": "fb_exchange_token", "client_id": APP_ID,
        "client_secret": secret, "fb_exchange_token": tok_user})
    tok_dai = (r or {}).get("access_token")
    if not tok_dai:
        print("✗ Không đổi được: %s"
              % (loi or (r or {}).get("error", {}).get("message", r)), file=sys.stderr)
        return 1
    d1, m1 = mo_ta(tok_dai)
    print("✓ %s" % (m1 if d1 else "đổi xong nhưng không mô tả được"))

    print("\nB2. Xin page token bằng token dài hạn…")
    r2, loi2 = goi("/%s" % PAGE_ID, {"fields": "access_token,name", "access_token": tok_dai})
    tok_page = (r2 or {}).get("access_token")
    if not tok_page:
        print("✗ Không lấy được page token: %s"
              % (loi2 or (r2 or {}).get("error", {}).get("message", r2)), file=sys.stderr)
        return 1

    d2, m2 = mo_ta(tok_page)
    if not d2:
        print("✗ Page token không dùng được: %s" % m2, file=sys.stderr)
        return 1
    print("✓ %s" % m2)

    if d2.get("expires_at") != 0:
        print("✗ Page token VẪN CÓ HẠN — chưa đạt, KHÔNG ghi đè token đang lưu.",
              file=sys.stderr)
        print("  Thường vì bước B1 trả lại đúng token ngắn hạn (user token gốc đã quá hạn).",
              file=sys.stderr)
        return 1

    ghi(tok_page)
    print("\n✓ XONG — page token vĩnh viễn, độ dài %d ký tự." % len(tok_page))
    return 0


if __name__ == "__main__":
    sys.exit(main())
