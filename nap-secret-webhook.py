#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nạp secret Facebook + Anthropic vào Edge Function webhook Messenger.

    python3 /Users/Huy/Claude/App/HuongDienWork/nap-secret-webhook.py

Đọc khoá từ `~/.config/api-keys.env` (do 2 script `cam-*-key-hdw.py` ghi), đẩy
lên Supabase, rồi GỌI THẬT function để nghiệm thu — không tin lời khai "Finished
secrets set" của CLI.

KHÔNG in giá trị secret ra màn hình, chỉ in độ dài (mục 14c CLAUDE.md).
File tạm chứa secret đặt ở `~/.config` quyền 600 rồi xoá ngay, KHÔNG để `/tmp`
vì `/tmp` là thư mục dùng chung, mọi tài khoản trên máy đọc được (mục 18 lớp 6).
"""

import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

FILE_ENV = Path.home() / ".config" / "api-keys.env"
TAM = Path.home() / ".config" / ".hdw-secrets-tam.env"
PROJECT_REF = "ltmlueqkajqmduoqghdf"
URL_FN = f"https://{PROJECT_REF}.supabase.co/functions/v1/messenger-webhook"

# tên secret trên Supabase  →  tên khoá trong api-keys.env
ANH_XA = {
    "FB_APP_SECRET": "FB_APP_SECRET_HDW",
    "FB_PAGE_ACCESS_TOKEN": "FB_PAGE_ACCESS_TOKEN_HDW",
    "FB_WEBHOOK_VERIFY_TOKEN": "FB_WEBHOOK_VERIFY_TOKEN_HDW",
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY_HDW",
}


def doc_env() -> dict:
    if not FILE_ENV.exists():
        return {}
    ra = {}
    for dong in FILE_ENV.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)$", dong)
        if m and m.group(2).strip():
            ra[m.group(1)] = m.group(2).strip()
    return ra


def main() -> int:
    env = doc_env()
    thieu = [k for k in ANH_XA.values() if k not in env]
    if thieu:
        print(f"✗ Thiếu {len(thieu)} khoá trong {FILE_ENV}: {', '.join(thieu)}",
              file=sys.stderr)
        print("  Chạy trước:", file=sys.stderr)
        print("    python3 /Users/Huy/Claude/App/HuongDienWork/cam-facebook-key-hdw.py",
              file=sys.stderr)
        print("    python3 /Users/Huy/Claude/App/HuongDienWork/cam-anthropic-key-hdw.py",
              file=sys.stderr)
        return 1

    token = env.get("SUPABASE_ACCESS_TOKEN_HDW")
    if not token:
        print(f"✗ Thiếu SUPABASE_ACCESS_TOKEN_HDW trong {FILE_ENV}", file=sys.stderr)
        print("  Chạy: python3 /Users/Huy/Claude/App/HuongDienWork/"
              "cam-supabase-token-hdw.py", file=sys.stderr)
        return 1

    for ten, khoa in ANH_XA.items():
        print(f"  {ten}: {len(env[khoa])} ký tự")

    TAM.write_text("".join(f"{t}={env[k]}\n" for t, k in ANH_XA.items()), encoding="utf-8")
    os.chmod(TAM, 0o600)
    try:
        r = subprocess.run(
            ["npx", "--yes", "supabase@latest", "secrets", "set",
             "--project-ref", PROJECT_REF, "--env-file", str(TAM)],
            capture_output=True, text=True, timeout=300,
            env={**os.environ, "SUPABASE_ACCESS_TOKEN": token},
        )
    finally:
        TAM.unlink(missing_ok=True)

    if r.returncode != 0:
        print(f"✗ Nạp secret trượt (mã {r.returncode}): {r.stderr.strip()[:300]}",
              file=sys.stderr)
        return 1
    print("✓ Đã đẩy 4 secret lên Supabase")

    # ── Nghiệm thu bằng lời gọi THẬT. CLI báo "Finished" không chứng minh được
    #    function đọc được secret — hai chuyện khác nhau, và chênh nhau đúng ở
    #    chỗ hay hỏng nhất (sai tên biến, function chưa deploy lại).
    thu = "zim-thu-nghiem-" + os.urandom(4).hex()
    q = urllib.parse.urlencode({
        "hub.mode": "subscribe",
        "hub.verify_token": thu,          # CỐ TÌNH sai
        "hub.challenge": "12345",
    })
    r2 = subprocess.run(["curl", "-s", "-w", "\n%{http_code}", f"{URL_FN}?{q}",
                         "--max-time", "30"], capture_output=True, text=True, timeout=60)
    than, _, ma = r2.stdout.rpartition("\n")
    ma = ma.strip()

    if ma == "500" and "thiếu secret" in than:
        print(f"✗ Function VẪN báo thiếu secret: {than.strip()[:200]}", file=sys.stderr)
        print("  Nhiều khả năng function chưa deploy lại sau khi đổi tên biến.",
              file=sys.stderr)
        return 1
    if ma != "403":
        print(f"✗ Chờ mã 403 (verify token sai) nhưng nhận {ma}: {than.strip()[:200]}",
              file=sys.stderr)
        return 1

    print("✓ Nghiệm thu: verify token SAI bị từ chối đúng mã 403 — function đã đọc"
          " được secret")
    print("\nBước cuối, làm trên developers.facebook.com (App ID 994076413665016)")
    print("→ Messenger → Webhooks:")
    print(f"  Callback URL : {URL_FN}")
    print("  Verify Token : đúng chuỗi đã cắm vào FB_WEBHOOK_VERIFY_TOKEN_HDW")
    print("  Bấm Verify and Save, rồi Subscribe cho Page Hương Diện Baby Mart với")
    print("  3 trường: messages · messaging_postbacks · message_echoes")
    print("  (thiếu message_echoes thì van an toàn không biết nhân viên đã trả lời")
    print("   tay, bộ đếm không reset và khách bị chuyển tay oan sau 3 lượt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
