#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cắm Supabase Access Token — để Zim tự deploy Edge Function webhook Messenger.

Chạy:  python3 /Users/Huy/Claude/App/HuongDienWork/cam-supabase-token-hdw.py

Lấy token ở đâu: https://supabase.com/dashboard/account/tokens
→ "Generate new token" → đặt tên gì cũng được (vd "claude-deploy") → Copy.
Token chỉ hiện MỘT LẦN, copy xong mới đóng cửa sổ.

Script làm (mục 14c CLAUDE.md — không hỏi secret qua chat):
  1. Hỏi token bằng getpass (không hiện màn hình, không vào lịch sử shell).
  2. Gọi thử Management API, in ra TÊN các project token này với tới được —
     nếu không thấy project ltmlueqkajqmduoqghdf thì báo sai và KHÔNG ghi gì.
  3. Ghi vào ~/.config/api-keys.env, quyền 600.
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
KHOA = "SUPABASE_ACCESS_TOKEN_HDW"
PROJECT_REF = "ltmlueqkajqmduoqghdf"
API = "https://api.supabase.com/v1/projects"


def thu_token(token):
    """Gọi Management API, trả (được, mô tả). KHÔNG in token ra màn hình."""
    try:
        r = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}", API,
             "-H", f"Authorization: Bearer {token}", "--max-time", "30"],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, "gọi Supabase quá 60 giây không trả lời"
    if r.returncode != 0:
        return False, f"curl thoát mã {r.returncode}: {r.stderr.strip()[:200]}"

    than, _, ma = r.stdout.rpartition("\n")
    if ma.strip() != "200":
        return False, f"Supabase trả mã {ma.strip()}: {than[:200]}"
    try:
        ds = json.loads(than)
    except json.JSONDecodeError:
        return False, f"Supabase trả về thứ không phải JSON: {than[:200]}"

    refs = {p.get("id"): p.get("name") for p in ds if isinstance(p, dict)}
    if PROJECT_REF not in refs:
        return False, (f"token dùng được nhưng KHÔNG thấy project {PROJECT_REF}. "
                       f"Token này với tới: {', '.join(refs.values()) or '(không project nào)'}")
    return True, f"token sống — thấy project \"{refs[PROJECT_REF]}\" ({PROJECT_REF})"


def main():
    print(__doc__.split("Script làm")[0])
    print("=" * 70)

    dong = FILE_ENV.read_text(encoding="utf-8").splitlines() if FILE_ENV.exists() else []
    if any(re.match(rf"^\s*{re.escape(KHOA)}\s*=\s*\S", d) for d in dong):
        if input(f"{KHOA} đã có. Ghi đè? (g/K) ").strip().lower() != "g":
            return 0

    token = getpass.getpass("Supabase Access Token (gõ vào, màn hình sẽ KHÔNG hiện) → ").strip()
    if not token:
        print("✗ Trống.", file=sys.stderr)
        return 1
    print(f"  (đã nhận {len(token)} ký tự)")

    print("\nĐang kiểm token…")
    duoc, mo_ta = thu_token(token)
    if not duoc:
        print(f"✗ {mo_ta}", file=sys.stderr)
        print("  Chưa ghi gì vào file. Kiểm lại rồi chạy lại.", file=sys.stderr)
        return 1
    print(f"✓ {mo_ta}")

    if FILE_ENV.exists():
        sao_luu = FILE_ENV.with_suffix(".env.bak")
        shutil.copy2(FILE_ENV, sao_luu)
        os.chmod(sao_luu, 0o600)
        print(f"✓ Đã sao lưu bản cũ: {sao_luu}")

    ra, da_thay = list(dong), False
    for i, d in enumerate(ra):
        if re.match(rf"^\s*#?\s*{re.escape(KHOA)}\s*=", d):
            ra[i], da_thay = f"{KHOA}={token}", True
    if not da_thay:
        ra += ["", "# --- Supabase: deploy Edge Function chatbot Messenger Hương Diện ---",
               f"{KHOA}={token}"]

    FILE_ENV.parent.mkdir(parents=True, exist_ok=True)
    FILE_ENV.write_text("\n".join(ra) + "\n", encoding="utf-8")
    os.chmod(FILE_ENV, 0o600)
    print(f"✓ Đã ghi {FILE_ENV} (quyền 600), khoá {KHOA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
