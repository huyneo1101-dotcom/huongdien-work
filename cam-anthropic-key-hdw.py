#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cắm Anthropic API key riêng cho chatbot Messenger Hương Diện Baby Mart.

Chạy:  python3 /Users/Huy/Claude/App/HuongDienWork/cam-anthropic-key-hdw.py

Lấy key ở: https://console.anthropic.com/settings/keys — tạo key MỚI (đừng dùng lại
key của việc khác), và bật billing riêng cho tổ chức/dự án đó (khác hẳn gói Claude
Code đang dùng — key này bị trừ tiền theo lượt gọi API thật, không liên quan
subscription Claude Code).

Việc script làm (theo đúng mẫu cam-key-kiotviet.py — mục 14c CLAUDE.md, không hỏi
secret qua chat):
  1. Hỏi key bằng getpass (không hiện lên màn hình, không vào lịch sử shell).
  2. Gọi thử 1 request rẻ nhất (Haiku, max_tokens=1) để chắc key sống VÀ billing đã
     bật, trước khi ghi vào đĩa.
  3. Sao lưu file cũ, ghi/thay đúng dòng ANTHROPIC_API_KEY_HDW, đặt quyền 600.
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
URL_MESSAGES = "https://api.anthropic.com/v1/messages"
KHOA = "ANTHROPIC_API_KEY_HDW"


def thu_key(api_key: str):
    """Gọi thật Anthropic Messages API, model rẻ nhất, 1 token. Trả (được_không, mô_tả).

    Dùng curl chứ không dùng thư viện Python: máy Huy có thiết bị chèn cert ở giữa
    nên urllib/httpx hay trượt CERTIFICATE_VERIFY_FAILED, còn curl đọc keychain
    macOS nên qua được (cùng lý do đã ghi trong cam-key-kiotviet.py).
    """
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "hi"}],
    })
    try:
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", URL_MESSAGES,
             "-H", f"x-api-key: {api_key}",
             "-H", "anthropic-version: 2023-06-01",
             "-H", "Content-Type: application/json",
             "--data", body, "--max-time", "30"],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, "gọi Anthropic quá 60 giây không trả lời"
    if r.returncode != 0:
        return False, f"curl thoát mã {r.returncode}: {r.stderr.strip()[:200]}"
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False, f"Anthropic trả về thứ không phải JSON: {r.stdout[:200]}"
    if d.get("type") == "message":
        usage = d.get("usage", {})
        return True, f"gọi được, token vào/ra: {usage.get('input_tokens')}/{usage.get('output_tokens')}"
    loi = d.get("error", {})
    ma = loi.get("type", "?")
    thong_bao = loi.get("message", json.dumps(d, ensure_ascii=False)[:300])
    goi_y = ""
    if ma == "authentication_error":
        goi_y = " — key sai hoặc đã bị thu hồi"
    elif ma == "permission_error":
        goi_y = " — key đúng nhưng chưa có quyền gọi model này"
    elif ma == "billing_error" or "credit" in thong_bao.lower():
        goi_y = " — tổ chức chưa bật billing hoặc hết hạn mức, vào console.anthropic.com/settings/billing"
    return False, f"Anthropic từ chối ({ma}): {thong_bao}{goi_y}"


def doc_env():
    if not FILE_ENV.exists():
        return []
    return FILE_ENV.read_text(encoding="utf-8").splitlines()


def ghi_env(dong_cu, api_key):
    khop_dong = re.compile(rf"^\s*#?\s*{re.escape(KHOA)}\s*=")
    da_thay = False
    ra = []
    for dong in dong_cu:
        if khop_dong.match(dong):
            ra.append(f"{KHOA}={api_key}")
            da_thay = True
        else:
            ra.append(dong)
    if not da_thay:
        ra.append("")
        ra.append("# --- Anthropic API: chatbot Messenger Hương Diện (billing riêng, KHÔNG phải gói Claude Code) ---")
        ra.append(f"{KHOA}={api_key}")
    return ra


def main():
    print(__doc__.split("Việc script làm")[0])
    print("=" * 70)

    if FILE_ENV.exists() and any(re.match(rf"^\s*{re.escape(KHOA)}\s*=\s*\S", d) for d in doc_env()):
        if input(f"Đã có {KHOA} trong file — ghi đè? (g/K) ").strip().lower() != "g":
            return 0

    # Nhận qua CLIPBOARD trước, getpass chỉ là đường lùi. Key Anthropic hiện đúng
    # MỘT LẦN lúc tạo rồi mất, mà trang có sẵn nút copy — bắt gõ lại vào ô ẩn là
    # chỗ dễ hụt nhất. Hàm chờ nằm ở congcu/cho_clipboard.py, CẤM chép về đây
    # (mục 17 CLAUDE.md: một hàm duy nhất, nơi khác GỌI).
    sys.path.insert(0, "/Users/Huy/Claude/congcu")
    try:
        from cho_clipboard import boc_tien_to, cho
    except ImportError as e:                                      # noqa: BLE001
        print("⚠️  Không nạp được cho_clipboard (%s) — lùi về gõ tay." % e)
        api_key = ""
    else:
        api_key, loi = cho(boc_tien_to("sk-ant-", 40), ten="Anthropic API key")
        if loi:
            print("⚠️  %s — lùi về gõ tay." % loi)
            api_key = ""

    if not api_key:
        api_key = getpass.getpass("Anthropic API key (gõ vào, màn hình sẽ KHÔNG hiện) → ").strip()
    if not api_key:
        print("✗ Key trống.", file=sys.stderr)
        return 1
    if not api_key.startswith("sk-ant-"):
        print("⚠️  Key không bắt đầu bằng 'sk-ant-' — có thể dán nhầm thứ khác.", file=sys.stderr)
        if input("Vẫn thử? (d/K) ").strip().lower() != "d":
            return 1

    print("\nĐang gọi thử Anthropic để chắc key sống và billing đã bật…")
    duoc, mo_ta = thu_key(api_key)
    if not duoc:
        print(f"✗ Key KHÔNG dùng được: {mo_ta}", file=sys.stderr)
        print("  Chưa ghi gì vào file. Kiểm lại key/billing rồi chạy lại.", file=sys.stderr)
        return 1
    print(f"✓ Key sống — {mo_ta}")

    dong = doc_env()
    if FILE_ENV.exists():
        sao_luu = FILE_ENV.with_suffix(".env.bak")
        shutil.copy2(FILE_ENV, sao_luu)
        os.chmod(sao_luu, 0o600)
        print(f"✓ Đã sao lưu bản cũ: {sao_luu}")

    FILE_ENV.parent.mkdir(parents=True, exist_ok=True)
    FILE_ENV.write_text("\n".join(ghi_env(dong, api_key)) + "\n", encoding="utf-8")
    os.chmod(FILE_ENV, 0o600)
    print(f"✓ Đã ghi {FILE_ENV} (quyền 600), khoá {KHOA}")
    print("\nXong. Checklist 'Anthropic API key' trong quy-trinh-chatbot-messenger.md coi như đã đủ điều kiện.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
