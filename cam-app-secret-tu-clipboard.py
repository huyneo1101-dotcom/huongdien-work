#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nhận Facebook App Secret TỪ CLIPBOARD rồi đổi Page Access Token sang VĨNH VIỄN.

Chạy:  python3 /Users/Huy/Claude/App/HuongDienWork/cam-app-secret-tu-clipboard.py

Khác `cam-app-secret-va-token-vinh-vien.py` ở đúng một chỗ: script kia bắt gõ lại
secret qua `getpass`, script này đọc thẳng từ clipboard — copy xong bấm Run là hết
việc, không phải dán vào ô ẩn rồi lo gõ nhầm.

Secret đi thẳng clipboard → file, KHÔNG qua khung chat, KHÔNG in ra màn hình
(mục 14c CLAUDE.md). Chẩn đoán chỉ in ĐỘ DÀI và thứ Facebook trả về.

Sai ở bước nào cũng DỪNG, không ghi bậy:
  (i) clipboard không có dạng App Secret · (ii) App ID/Secret không khớp
  (iii) không đổi được token · (iv) token mới không dùng được.
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
KHOA_SECRET = "FB_APP_SECRET_HDW"
KHOA_TOKEN = "FB_PAGE_ACCESS_TOKEN_HDW"


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


def ta_hinh_dang(s):
    """Mô tả clipboard bằng ĐẶC ĐIỂM, tuyệt đối không in giá trị (mục 14c).

    Có mặt vì thông báo "dài 74" một mình không đủ để biết đang copy nhầm thứ gì —
    đã vấp thật 31/07/2026, phải đoán mò giữa client token, URL và cả dòng dính nhãn.
    """
    loai = ("hex thường" if re.fullmatch(r"[0-9a-f]+", s) else
            "hex có chữ hoa" if re.fullmatch(r"[0-9a-fA-F]+", s) else
            "có ký tự ngoài hex")
    la = sorted(set(re.sub(r"[0-9a-fA-F]", "", s)))
    return "dài %d, %s%s%s%s" % (
        len(s), loai,
        ", có khoảng trắng bên trong" if re.search(r"\s", s) else "",
        ", %d dòng" % (s.count("\n") + 1) if "\n" in s else "",
        ", ký tự lạ: %r" % ("".join(la)[:20],) if la else "")


def doc_clipboard():
    """App Secret là chuỗi hex 32 ký tự. Kiểm hình dạng trước khi gọi mạng.

    Nới có chủ ý so với bản đầu: chấp nhận chữ HOA và tự BÓC chuỗi 32-hex nằm lẫn
    trong chuỗi lớn (copy dính nhãn, dính khoảng trắng, dính xuống dòng) — bắt copy
    lại cho đúng từng ký tự là đẩy việc về phía người dùng ở chỗ máy tự làm được.

    ⚠ Vẫn cố ý KHÔNG chấp nhận chuỗi bắt đầu bằng EAA: đó là access token, và nhầm
    hai thứ này là lỗi hay gặp nhất vì cùng copy từ một trang.
    ⚠ Tìm thấy NHIỀU chuỗi 32-hex thì DỪNG, không tự chọn — chọn nhầm là ghi một
    secret sai vào file rồi đi tìm nguyên nhân ở chỗ khác.
    """
    r = subprocess.run(["pbpaste"], capture_output=True, text=True)
    if r.returncode != 0:
        return None, "không đọc được clipboard (pbpaste thoát mã %d)" % r.returncode
    v = r.stdout.strip()
    if not v:
        return None, "clipboard rỗng"
    if v.startswith("EAA"):
        return None, "clipboard đang là ACCESS TOKEN, không phải App Secret"

    if re.fullmatch(r"[0-9a-fA-F]{32}", v):
        return v.lower(), None

    ung_vien = sorted(set(m.lower() for m in re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])", v)))
    if len(ung_vien) == 1:
        print("⚠ Clipboard %s — đã bóc ra chuỗi 32 ký tự hex nằm bên trong."
              % ta_hinh_dang(v))
        return ung_vien[0], None
    if len(ung_vien) > 1:
        return None, ("clipboard chứa %d chuỗi 32-hex khác nhau, không đoán được cái nào "
                      "là App Secret (%s)" % (len(ung_vien), ta_hinh_dang(v)))
    return None, ("clipboard không có dạng App Secret và không chứa chuỗi 32-hex nào "
                  "(%s)" % ta_hinh_dang(v))


def mo_ta_token(tok):
    d, loi = goi("/debug_token", {"input_token": tok, "access_token": tok})
    if loi:
        return None, loi
    d = (d or {}).get("data", {})
    if not d.get("is_valid"):
        return None, "token không hợp lệ"
    han = "KHÔNG hết hạn" if d.get("expires_at") == 0 else "hết hạn lúc %s" % d.get("expires_at")
    return d, "type=%s, Page id %s, %s, quyền: %s" % (
        d.get("type"), d.get("profile_id"), han, ", ".join(d.get("scopes", [])))


def ghi(gia_tri: dict):
    dong = FILE_ENV.read_text(encoding="utf-8").splitlines() if FILE_ENV.exists() else []
    if FILE_ENV.exists():
        sl = FILE_ENV.with_suffix(".env.bak")
        shutil.copy2(FILE_ENV, sl)
        os.chmod(sl, 0o600)
        print("✓ Đã sao lưu bản cũ: %s" % sl)
    da_thay = set()
    for i, d in enumerate(dong):
        for k in gia_tri:
            if re.match(r"^\s*#?\s*%s\s*=" % re.escape(k), d):
                dong[i] = "%s=%s" % (k, gia_tri[k])
                da_thay.add(k)
    thieu = [k for k in gia_tri if k not in da_thay]
    if thieu:
        dong.append("")
        for k in thieu:
            dong.append("%s=%s" % (k, gia_tri[k]))
    FILE_ENV.parent.mkdir(parents=True, exist_ok=True)
    FILE_ENV.write_text("\n".join(dong) + "\n", encoding="utf-8")
    os.chmod(FILE_ENV, 0o600)
    print("✓ Đã ghi %s vào %s (quyền 600)" % (", ".join(gia_tri), FILE_ENV))


def doc_khoa(ten):
    if not FILE_ENV.exists():
        return None
    for d in FILE_ENV.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*%s\s*=\s*(.+)$" % re.escape(ten), d)
        if m:
            return m.group(1).strip()
    return None


def cho_clipboard(tran_giay=180, nhip=2):
    """Đọc clipboard ngay; chưa có App Secret thì CHỜ tới khi người dùng copy.

    ⚠ Vì sao phải chờ chứ không đọc một phát rồi thoát (vấp thật 31/07/2026):
    script này được chạy bằng cách COPY dòng lệnh rồi dán vào terminal — thao tác
    đó GHI ĐÈ clipboard, xoá mất chính thứ script cần đọc. Lần chạy đầu nhận đúng
    74 ký tự của dòng lệnh gọi nó. Đọc-một-phát và chờ khác nhau ở chỗ: chờ thì
    thứ tự thao tác của người dùng không còn quan trọng.
    """
    v, loi = doc_clipboard()
    if not loi:
        return v, None
    print("Clipboard hiện chưa phải App Secret (%s)." % loi)
    print("→ Bây giờ sang Chrome copy 'Khóa bí mật của ứng dụng'. Script tự nhận,")
    print("  không phải quay lại đây bấm gì. Chờ tối đa %d giây…" % tran_giay)
    da = 0
    while da < tran_giay:
        time.sleep(nhip)
        da += nhip
        v, loi = doc_clipboard()
        if not loi:
            print("✓ Đã nhận được App Secret từ clipboard sau %d giây." % da)
            return v, None
        if da % 30 == 0:
            print("  …%d/%d giây, vẫn chưa thấy (%s)" % (da, tran_giay, loi))
    return None, "hết %d giây chờ mà clipboard vẫn chưa có App Secret" % tran_giay


def main():
    secret, loi = cho_clipboard()
    if loi:
        print("✗ %s" % loi, file=sys.stderr)
        print("  Copy 'Khóa bí mật của ứng dụng' ở developers.facebook.com rồi chạy lại.",
              file=sys.stderr)
        return 1
    print("Clipboard: chuỗi 32 ký tự hex — đang kiểm với Facebook…")

    r, loi = goi("/oauth/access_token", {
        "client_id": APP_ID, "client_secret": secret, "grant_type": "client_credentials"})
    if loi or not (r or {}).get("access_token"):
        print("✗ App ID/Secret không khớp: %s"
              % (loi or (r or {}).get("error", {}).get("message", r)), file=sys.stderr)
        print("  Chưa ghi gì vào file.", file=sys.stderr)
        return 1
    print("✓ App ID/Secret khớp nhau (secret dài %d ký tự)" % len(secret))

    tok_ngan = doc_khoa(KHOA_TOKEN)
    if not tok_ngan:
        print("⚠ Chưa có %s để đổi — chỉ ghi App Secret." % KHOA_TOKEN)
        ghi({KHOA_SECRET: secret})
        return 0

    print("\nĐang đổi token sang bản dài hạn…")
    r, loi = goi("/oauth/access_token", {
        "grant_type": "fb_exchange_token", "client_id": APP_ID,
        "client_secret": secret, "fb_exchange_token": tok_ngan})
    tok_dai = (r or {}).get("access_token")
    if not tok_dai:
        print("✗ Không đổi được: %s" % (loi or (r or {}).get("error", {}).get("message", r)),
              file=sys.stderr)
        print("  Vẫn ghi App Secret để dùng cho bước sau.", file=sys.stderr)
        ghi({KHOA_SECRET: secret})
        return 1

    # Page token vĩnh viễn phải lấy lại qua chính Page bằng token dài hạn — kết quả
    # của bước exchange có thể vẫn là bản có hạn.
    r2, _ = goi("/%s" % PAGE_ID, {"fields": "access_token,name", "access_token": tok_dai})
    tok_page = (r2 or {}).get("access_token") or tok_dai

    d2, mo_ta2 = mo_ta_token(tok_page)
    if not d2:
        print("✗ Token sau khi đổi không dùng được: %s" % mo_ta2, file=sys.stderr)
        ghi({KHOA_SECRET: secret})
        return 1
    print("✓ Token mới: %s" % mo_ta2)
    if d2.get("expires_at") != 0:
        print("⚠ Token mới VẪN CÓ HẠN — Facebook chưa cấp bản vĩnh viễn.")
        print("  Thường vì token gốc đã quá hạn. Lấy token mới ở Graph API Explorer,")
        print("  chạy cam-page-token-tu-clipboard.py, rồi chạy lại script này.")

    ghi({KHOA_SECRET: secret, KHOA_TOKEN: tok_page})
    return 0


if __name__ == "__main__":
    sys.exit(main())
