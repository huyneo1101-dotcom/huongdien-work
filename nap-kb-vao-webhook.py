#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nạp knowledge base của shop vào Edge Function webhook Messenger.

    python3 /Users/Huy/Claude/App/HuongDienWork/nap-kb-vao-webhook.py
    python3 /Users/Huy/Claude/App/HuongDienWork/nap-kb-vao-webhook.py --tu-kiem

Đọc `HuongDien/kb-prenny/knowledge-base.md` (do `gop-knowledge-base.py` sinh ra)
rồi ghi thành `kb.ts` cho Edge Function. Sinh ra file .ts thay vì đọc file .md
lúc chạy vì Supabase chỉ đóng gói mã nguồn của function, không đóng gói file
nằm ngoài thư mục đó.

CỔNG CHẶN — knowledge base có SỐ CÓ TUỔI THỌ thì TỪ CHỐI nạp:
`gop-knowledge-base.py` đã lọc giá/khuyến mãi/tồn kho ở đầu nguồn, nhưng file
đó do phiên khác ghi và còn sửa tiếp. Prompt là thứ sửa chậm và ít ai rà lại —
lọt một bảng giá vào đây là bot báo giá sai cho khách mà không ai biết, cho tới
khi có người phàn nàn. Cổng này chặn ở cuối nguồn, chấp nhận chặn oan còn hơn
để số cũ đi thẳng ra khách.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

NGUON = Path("/Users/Huy/Claude/HuongDien/kb-prenny/knowledge-base.md")
DICH = Path("/Users/Huy/Claude/App/HuongDienWork/supabase/functions/"
            "messenger-webhook/kb.ts")

# Ngưỡng: đoạn nào chạm một trong các mẫu này là có tuổi thọ.
#
# ⚠ MẤY MẪU DƯỚI ĐÃ SIẾT LẠI SAU KHI ĐO TRÊN FILE THẬT (31/07/2026). Bản đầu
# dùng mẫu rộng `\bcòn\s+hàng\b` và mẫu ngày trần, chạy lên `knowledge-base.md`
# thật thì chặn 4 chỗ và CẢ 4 ĐỀU OAN: 01 dòng ghi chú ngày sinh file, 01 câu
# dặn model ("không tự khẳng định còn hàng"), 02 CÂU HỎI CỦA KHÁCH trong danh
# mục FAQ ("Bên em còn hàng không"). Cổng nào luôn phải mở cờ mới qua được là
# cổng chết — nó dạy người dùng phản xạ mở cờ, rồi mọi cổng còn lại mất giá trị
# theo. Bốn dòng đó nay là ca đối chứng 12–15, lấy nguyên văn từ file thật.
MAU_CAM = [
    # Giá tiền: "250.000đ", "250k", "250 000 vnđ"
    (r"\d[\d.\s]{2,}\s*(?:đ\b|vnđ|vnd|₫)", "giá tiền"),
    (r"\b\d{2,4}\s*k\b(?!g)", "giá tiền viết tắt (k)"),
    # Mốc tháng/năm kiểu bảng giá: "T10/2025".
    (r"\b[Tt]\s*\d{1,2}\s*/\s*20\d{2}\b", "mốc tháng/năm"),
    # Ngày cụ thể chỉ tính khi ĐI KÈM ngữ cảnh giá/khuyến mãi/hiệu lực — ngày
    # trần còn là ngày sinh file, ngày cập nhật tài liệu, vô hại.
    (r"(?:giá|khuyến\s*mãi|ưu\s*đãi|áp\s*dụng|hiệu\s*lực|hết\s*hạn|"
     r"từ\s*ngày|đến\s*ngày|kéo\s*dài)[^\n]{0,60}?"
     r"\b\d{1,2}\s*/\s*\d{1,2}\s*/\s*20\d{2}\b", "mốc ngày của giá/khuyến mãi"),
    # Khai tồn kho cứng. Phải bắt "đang tạm hết men vi sinh" (dòng 39 KBHL) chứ
    # không chỉ "hết hàng" — đó là câu khiến bot nói sai trong khi KiotViet vẫn
    # còn hàng.
    (r"\b(?:đang\s+)?tạm\s+hết\b", "khai tạm hết mặt hàng"),
    # Có chủ ngữ shop đứng trước mới là LỜI KHAI. "Bên em còn hàng không" là
    # câu hỏi của khách, phải để yên — lọc câu hỏi ở `la_cau_hoi()`.
    (r"\b(?:nhà\s+em|bên\s+em|shop|cửa\s+hàng)\s+(?:đang\s+|vẫn\s+)?"
     r"(?:còn|hết)\s+hàng\b", "khai còn/hết hàng"),
    (r"còn\s+\d+\s+(?:hộp|lon|bịch|gói|thùng)", "khai số lượng tồn"),
]


def la_cau_hoi(dong: str) -> bool:
    """Câu hỏi mẫu của khách trong danh mục FAQ, không phải lời khai của shop."""
    d = chuan(dong).strip().rstrip("*_ ").lower()
    return d.endswith("?") or d.endswith("không") or d.endswith("ko")


def chuan(s: str) -> str:
    """NFC trước mọi phép so khớp tiếng Việt (macOS trả NFD)."""
    return unicodedata.normalize("NFC", s)


def soi(noi_dung: str):
    """Trả danh sách (số dòng, loại, trích) của mọi chỗ vi phạm."""
    ra = []
    for i, dong in enumerate(chuan(noi_dung).splitlines(), 1):
        if la_cau_hoi(dong):
            continue
        for mau, ten in MAU_CAM:
            m = re.search(mau, dong, re.IGNORECASE)
            if m:
                ra.append((i, ten, dong.strip()[:120]))
                break
    return ra


def dung_kb_ts(noi_dung: str) -> str:
    # Backtick và ${ phải thoát, kẻo vỡ template literal của TypeScript.
    an_toan = noi_dung.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    return (
        "// Knowledge base sinh TỰ ĐỘNG — ĐỪNG SỬA TAY, sẽ bị ghi đè.\n"
        "//\n"
        f"// Nguồn: {NGUON}\n"
        "// Sinh lại: python3 /Users/Huy/Claude/App/HuongDienWork/nap-kb-vao-webhook.py\n"
        "//\n"
        "// Rỗng thì bot vẫn chạy bằng phần tư vấn nền trong faq.ts, chỉ kém sâu hơn.\n"
        f"export const KB_NGOAI = `{an_toan}`;\n"
    )


def nap(bo_cong: bool = False) -> int:
    if not NGUON.exists():
        print(f"✗ Không thấy {NGUON}", file=sys.stderr)
        print("  Chạy `python3 /Users/Huy/Claude/HuongDien/gop-knowledge-base.py` trước.",
              file=sys.stderr)
        return 1

    noi_dung = NGUON.read_text(encoding="utf-8")
    if noi_dung.strip() == "":
        print(f"✗ {NGUON} rỗng — không nạp.", file=sys.stderr)
        return 1

    vi_pham = soi(noi_dung)
    if vi_pham and not bo_cong:
        print(f"✗ CHẶN: knowledge base còn {len(vi_pham)} chỗ có tuổi thọ, "
              f"nạp vào prompt là bot nói sai mà không ai biết:", file=sys.stderr)
        for so, ten, trich in vi_pham[:15]:
            print(f"   dòng {so} · {ten} · {trich}", file=sys.stderr)
        if len(vi_pham) > 15:
            print(f"   … còn {len(vi_pham) - 15} chỗ nữa", file=sys.stderr)
        print("\n  Sửa ở GỐC (gop-knowledge-base.py), đừng vá tay file .md.", file=sys.stderr)
        print("  Chắc chắn mấy chỗ trên vô hại thì chạy lại kèm --bo-cong-tuoi-tho.",
              file=sys.stderr)
        return 2
    if vi_pham and bo_cong:
        print(f"⚠ ĐÃ MỞ CỔNG: bỏ qua {len(vi_pham)} chỗ có tuổi thọ theo yêu cầu.")

    DICH.parent.mkdir(parents=True, exist_ok=True)
    DICH.write_text(dung_kb_ts(noi_dung), encoding="utf-8")
    print(f"✓ Đã nạp {len(noi_dung):,} ký tự vào {DICH}")
    print("  Deploy lại function thì bot mới dùng bản mới:")
    print("  supabase functions deploy messenger-webhook "
          "--project-ref ltmlueqkajqmduoqghdf --no-verify-jwt")
    return 0


# ────────────────────────────────────────────────────────────────── tự kiểm
CA = [
    ("PHẢI CHẶN — bảng giá lọt vào", "Sữa Aptamil số 1: 550.000đ một lon.", True),
    ("PHẢI CHẶN — giá viết tắt k", "Combo ăn dặm chỉ 350k thôi ạ.", True),
    ("PHẢI CHẶN — mốc tháng/năm", "Bảng giá áp dụng từ T10/2025.", True),
    ("PHẢI CHẶN — mốc ngày cụ thể", "Chương trình kéo dài tới 21/8/2025.", True),
    ("PHẢI CHẶN — khai hết hàng cứng", "Dạ nhà em đang tạm hết men vi sinh ạ.", True),
    ("PHẢI CHẶN — khai số lượng tồn", "Bên em còn 12 hộp bỉm size M.", True),
    ("[đối chứng] cân nặng KHÔNG phải giá",
     "Bỉm size M dùng cho bé 6 – 11 kg, size L cho bé 9 – 14 kg.", False),
    ("[đối chứng] tháng tuổi KHÔNG phải mốc thời gian",
     "Bé 6 tháng thì chuyển sang sữa số 2, bé 12 tháng chuyển số 3.", False),
    ("[đối chứng] tư vấn chăm sóc thuần, không số tiền",
     "Bé hay hăm thì mẹ thay bỉm 2 – 3 tiếng một lần và thoa kem chống hăm.", False),
    ("[đối chứng] 'k' trong kg không bị bắt nhầm",
     "Bé nặng 8 kg thì mẹ dùng size M ạ.", False),
    # File .md do Finder/Word chạm vào trả về NFD, chuỗi trong mã nguồn là NFC —
    # trông y hệt nhau, khác byte. Không chuẩn hoá thì cổng trượt CÂM đúng với
    # loại file hay dính nhất, mà bảng kết quả vẫn xanh.
    ("PHẢI CHẶN — cùng câu khai tồn kho nhưng viết dạng NFD",
     unicodedata.normalize("NFD", "Dạ nhà em đang tạm hết men vi sinh ạ."), True),

    # ── Ca 12–15: BỐN DÒNG THẬT mà bản cổng đầu tiên chặn OAN, lấy nguyên văn
    # từ `kb-prenny/knowledge-base.md` lúc 14:37 ngày 31/07/2026. Ca tự bịa
    # không thấy được mấy dòng này — chỉ chạy trên dữ liệu thật mới lộ ra.
    ("[đối chứng THẬT] dòng ghi chú ngày sinh file, không phải hạn của giá",
     "*Gộp từ dữ liệu Prenny AI (KBHL + KBSALE) ngày 31/07/2026. Đã gỡ mọi nội "
     "dung có tuổi thọ — giá, khuyến mãi, trạng thái kho.*", False),
    ("[đối chứng THẬT] câu DẶN model, không phải lời khai tồn kho",
     "- Không tự báo giá và không tự khẳng định còn hàng — luôn tra KiotViet "
     "trước khi trả lời.", False),
    ("[đối chứng THẬT] câu HỎI của khách trong danh mục FAQ (in đậm)",
     "**Bên em còn hàng  không**", False),
    ("[đối chứng THẬT] câu hỏi của khách có đánh số thứ tự",
     "7. Còn hàng này không", False),
    # Chiều ngược của ca 14/15: cùng cụm "còn hàng" nhưng là LỜI KHAI của shop.
    ("PHẢI CHẶN — shop tự khai còn hàng (chiều ngược của ca 14/15)",
     "Dạ bên em vẫn còn hàng size M ạ.", True),
    ("PHẢI CHẶN — ngày cụ thể ĐI KÈM khuyến mãi (chiều ngược của ca 12)",
     "Chương trình ưu đãi áp dụng từ ngày 21/8/2025.", True),
]

BAN_HONG = [
    # Nhắm thẳng `soi()` chứ không nhắm `nap()`: bộ ca gọi `soi()`, nên một bản
    # hỏng gỡ cổng trong `nap()` sẽ không có ca nào đi qua — đã vấp thật lúc dựng.
    ("bỏ hẳn cổng soi tuổi thọ",
     "        if la_cau_hoi(dong):\n            continue\n        for mau, ten in MAU_CAM:",
     "        if la_cau_hoi(dong):\n            continue\n        for mau, ten in []:",
     [1, 2, 3, 4, 5, 6, 11, 16, 17]),
    # Hai lớp cùng chống chặn oan nhưng đỡ HAI ca khác nhau, không chồng nhau:
    # ca 14 ("Bên em còn hàng không") có chủ ngữ shop nên chỉ lớp lọc câu hỏi
    # cứu được; ca 15 ("Còn hàng này không") không có chủ ngữ nên mẫu hẹp đã đỡ
    # sẵn, gỡ lớp lọc không đụng tới nó. Khai [14,15] là khai thừa, `--tu-kiem`
    # sẽ báo trượt vì lý do sai — con số dưới đây lấy từ lần chạy thật.
    ("bỏ lớp lọc câu hỏi của khách", "        if la_cau_hoi(dong):\n            continue\n",
     "", [14]),
    # Gỡ CẢ HAI lớp thì mới đỏ cả hai ca — bản hỏng này canh đúng hành vi
    # "câu hỏi của khách không phải lời khai của shop".
    ("gỡ cả lớp lọc câu hỏi lẫn phép đòi chủ ngữ shop",
     ["        if la_cau_hoi(dong):\n            continue\n",
      r'    (r"\b(?:nhà\s+em|bên\s+em|shop|cửa\s+hàng)\s+(?:đang\s+|vẫn\s+)?"'
      '\n     r"(?:còn|hết)\\s+hàng\\b", "khai còn/hết hàng"),'],
     ["",
      r'    (r"\bcòn\s+hàng\b|\bhết\s+hàng\b", "khai còn/hết hàng"),'],
     [14, 15]),
    # Chiều NỚI của phép siết: quay về mẫu `còn hàng` trần không cần chủ ngữ shop.
    # Đây đúng là bản cổng đầu tiên đã chặn oan 4/4 trên file thật.
    ("nới mẫu tồn kho về `còn hàng` trần (bản cổng đầu tiên)",
     r'    (r"\b(?:nhà\s+em|bên\s+em|shop|cửa\s+hàng)\s+(?:đang\s+|vẫn\s+)?"'
     '\n     r"(?:còn|hết)\\s+hàng\\b", "khai còn/hết hàng"),',
     r'    (r"\bcòn\s+hàng\b|\bhết\s+hàng\b", "khai còn/hết hàng"),',
     [13]),
    ("bỏ mẫu bắt giá tiền",
     '    (r"\\d[\\d.\\s]{2,}\\s*(?:đ\\b|vnđ|vnd|₫)", "giá tiền"),',
     '    (r"KHONG_BAO_GIO_KHOP_XXX", "giá tiền"),',
     [1]),
    ("bỏ mẫu bắt mốc ngày của giá/khuyến mãi",
     '     r"\\b\\d{1,2}\\s*/\\s*\\d{1,2}\\s*/\\s*20\\d{2}\\b", "mốc ngày của giá/khuyến mãi"),',
     '     r"KHONG_BAO_GIO_KHOP_YYY", "mốc ngày của giá/khuyến mãi"),',
     [4, 17]),
    ("nới mẫu giá viết tắt: bắt cả 'k' trong kg (chặn oan)",
     '    (r"\\b\\d{2,4}\\s*k\\b(?!g)", "giá tiền viết tắt (k)"),',
     '    (r"\\b\\d{1,4}\\s*k", "giá tiền viết tắt (k)"),',
     [10]),
    # Neo kèm dòng docstring phía trên: chuỗi neo trần nằm cùng file với chính
    # bảng khai này nên tự khớp 2 chỗ, và phép thay bị từ chối.
    ("bỏ chuẩn hoá NFC trước khi so khớp",
     '"""NFC trước mọi phép so khớp tiếng Việt (macOS trả NFD)."""\n'
     '    return unicodedata.normalize("NFC", s)',
     '"""NFC trước mọi phép so khớp tiếng Việt (macOS trả NFD)."""\n'
     "    return s",
     [11]),
]


def chay_ca(ham_soi) -> list:
    do = []
    for i, (ten, van, phai_chan) in enumerate(CA, 1):
        bi_chan = len(ham_soi(van)) > 0
        ok = bi_chan == phai_chan
        print(f"  {'✓' if ok else '✗'} [{i}] {ten}")
        if not ok:
            do.append(i)
    return do


def tu_kiem() -> int:
    print(f"=== BỘ TEST CỔNG NẠP KNOWLEDGE BASE — {len(CA)} ca ===\n")
    do = chay_ca(soi)
    print(f"\n{len(CA) - len(do)}/{len(CA)} ca đạt" + (f" — KHÔNG ĐẠT: {do}" if do else ""))

    print("\n=== TỰ KIỂM: dựng bản hỏng, khẳng định ca tương ứng phải ĐỎ ===\n")
    goc = Path(__file__)
    nguon = goc.read_text(encoding="utf-8")
    truot = 0

    for ten, tim, thay, phai_do in BAN_HONG:
        # Một bản hỏng có thể phải gỡ NHIỀU lớp cùng bảo vệ một hành vi — gỡ một
        # lớp thì lớp kia gánh và ca vẫn xanh (mục 17 CLAUDE.md).
        cap = list(zip(tim, thay)) if isinstance(tim, list) else [(tim, thay)]
        hong, xau = nguon, False
        for t, th in cap:
            dem = hong.count(t)
            if dem != 1:
                print(f"✗ [{ten}] chuỗi neo khớp {dem} chỗ (phải đúng 1)")
                truot += 1
                xau = True
                break
            hong = hong.replace(t, th)
        if xau:
            continue
        # Tên bản hỏng mang PID + sha1 nội dung: hai bản hỏng khác nhau luôn ra
        # hai đường dẫn khác nhau, không đụng bytecode cache của nhau.
        import hashlib
        import os
        vet = hashlib.sha1(hong.encode()).hexdigest()[:8]
        ban = goc.parent / f"_thu-hong-{os.getpid()}-{vet}-{goc.name}"
        ban.write_text(hong, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(ban), "--chi-ca"],
                               capture_output=True, text=True, timeout=120)
            do_that = [int(m) for m in re.findall(r"✗ \[(\d+)\]", r.stdout)]
            if len(do_that) == len(CA):
                print(f"✗ [{ten}] ĐỎ TOÀN BỘ {len(CA)} ca — phép thay hỏng cú pháp?")
                truot += 1
                continue
            thieu = [s for s in phai_do if s not in do_that]
            if phai_do and thieu:
                print(f"✗ [{ten}] ca {thieu} VẪN XANH — đỏ thực tế: {do_that}")
                truot += 1
            elif not phai_do and do_that:
                print(f"✓ [{ten}] (không khai ca nào) đỏ: {do_that}")
            elif not phai_do:
                print(f"✓ [{ten}] (không khai ca nào, không ca nào đỏ — chỉ ghi vết)")
            else:
                print(f"✓ [{ten}] bắt được, đỏ: {do_that}")
        finally:
            ban.unlink(missing_ok=True)

    print(f"\n{'✅' if truot == 0 else '❌'} {len(BAN_HONG) - truot}/{len(BAN_HONG)} "
          f"bản hỏng bị bắt")
    return 0 if not do and truot == 0 else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tu-kiem", action="store_true")
    p.add_argument("--chi-ca", action="store_true", help="dùng nội bộ khi tự kiểm")
    p.add_argument("--bo-cong-tuoi-tho", action="store_true",
                   help="nạp dù knowledge base còn số có tuổi thọ (ghi vết ra màn hình)")
    a = p.parse_args()
    if a.chi_ca:
        return 1 if chay_ca(soi) else 0
    if a.tu_kiem:
        return tu_kiem()
    return nap(bo_cong=a.bo_cong_tuoi_tho)


if __name__ == "__main__":
    sys.exit(main())
