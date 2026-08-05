# Bàn giao backend: "Nhắc khách mua lại" (rebuy) từ KiotViet

> Giao diện đã dựng xong trong `index.html` (component `Reorder`, tab **Số liệu → Nhắc mua lại**).
> Nó đọc bảng Supabase **`kv_customer_reorder`**. Bảng đó CHƯA có — việc của backend là tạo bảng
> + mở rộng Edge Function `kiotviet-sync` để đổ dữ liệu vào.
>
> **File này viết cho một phiên Claude chạy TRÊN MÁY MAC** (nơi có thư mục `supabase/` ngoài git
> và `SUPABASE_ACCESS_TOKEN_HDW`). Phiên trên máy mây không làm được phần này.

## 0. Hợp đồng dữ liệu mà frontend đang chờ (KHÔNG được đổi tên cột)

Frontend gọi đúng câu này (xem `index.html`, component `Reorder`):

```
GET /rest/v1/kv_customer_reorder
  ?select=customer_name,phone,product_name,last_purchase_date,cycle_days
  &order=last_purchase_date.asc&limit=500
```

→ Bảng **bắt buộc** có các cột: `customer_name` (text), `phone` (text), `product_name` (text),
`last_purchase_date` (date), `cycle_days` (int). Thừa cột khác thì tuỳ, nhưng 5 cột này phải đúng tên.

Frontend tự tính: `ngày dự kiến hết = last_purchase_date + cycle_days`, và nhắc trước 3 ngày.
Nên backend chỉ cần đưa **lần mua cuối** + **chu kỳ ngày**, không cần tính hộ ngày nhắc.

## 1. Tạo bảng + RLS (chạy trong Supabase SQL editor)

```sql
create table if not exists public.kv_customer_reorder (
  customer_id       text,
  product_id        text,
  customer_name     text,
  phone             text,
  product_name      text,
  last_purchase_date date,
  cycle_days        int,
  purchases         int,          -- số lần mua (để biết chu kỳ đáng tin tới đâu)
  updated_at        timestamptz default now(),
  primary key (customer_id, product_id)
);
alter table public.kv_customer_reorder enable row level security;
```

**RLS: sao y policy của một bảng `kv_` đang chạy** (vd `kv_invoices`) để app dùng chung khoá.
App đọc bằng `apikey`/`Authorization` = anon key **+ header `x-hd-key`** (xem `index.html:2522`,
`hdKey()`), và các bảng `kv_*` hiện có một policy kiểm chính header đó. Mở `kv_invoices` xem policy
`select` của nó rồi tạo policy y hệt cho `kv_customer_reorder`. **Đừng để bảng mở toang** — nó chứa
tên + SĐT khách.

```sql
-- ví dụ, ĐỔI điều kiện cho khớp policy kv_invoices thật trên project:
create policy "hd read" on public.kv_customer_reorder for select
  using ( current_setting('request.headers',true)::json->>'x-hd-key' = current_setting('app.hd_key',true) );
```
(Câu trên chỉ là mẫu — **lấy đúng biểu thức từ policy `kv_invoices` hiện hành**, vì cơ chế kiểm khoá
Hương Diện đã dựng sẵn ở đó, chép sai là hoặc lộ dữ liệu hoặc app đọc ra rỗng.)

## 2. Mở rộng Edge Function `kiotviet-sync`

Function này đã có sẵn luồng lấy token KiotViet (từ secret `KV_RETAILER`/`KV_CLIENT_ID`/`KV_CLIENT_SECRET`)
và đã ghi các bảng `kv_invoices`, `kv_products`… **Đọc file thật `supabase/functions/kiotviet-sync/index.ts`
trước**, tái dùng hàm gọi API + client Supabase đã có, chỉ THÊM một bước tổng hợp. Đừng viết lại từ đầu.

### 2a. Kéo dữ liệu (KiotViet Public API — base `https://public.kiotapi.com`)

- **Khách hàng** — `GET /customers?pageSize=100&currentItem=...` (phân trang). Lấy `id`, `name`,
  `contactNumber`. Bỏ khách rỗng/"Khách lẻ".
- **Hoá đơn kèm dòng hàng** — `GET /invoices?pageSize=100&fromPurchaseDate=<180 ngày trước>&orderBy=purchaseDate&orderDirection=DESC&includeInvoiceDelivery=false`.
  Mỗi hoá đơn có `customerId`, `purchaseDate`, và mảng **`invoiceDetails`** (mỗi dòng: `productId`,
  `productName`, `quantity`). Phân trang tới khi hết. Chỉ lấy hoá đơn `status` hoàn tất (đã bán, không huỷ).

Cửa sổ 180 ngày là đủ để nhìn ra chu kỳ mua bỉm/sữa mà không kéo cả lịch sử. Chỉnh qua body
`{days:180}` nếu muốn (frontend đang gửi `{days:30}` cho luồng cũ — thêm nhánh riêng, đừng phá luồng cũ).

### 2b. Tổng hợp thành "lần mua cuối + chu kỳ" theo (khách, sản phẩm)

```
for mỗi hoá đơn (đã sắp theo purchaseDate):
  for mỗi dòng trong invoiceDetails:
     gom vào nhóm key = customerId + '|' + productId, đẩy ngày mua vào danh sách

for mỗi nhóm:
  ngày = sort(danh sách ngày mua)  // tăng dần
  last_purchase_date = ngày cuối
  purchases = số lần mua
  nếu purchases >= 2:
     các khoảng = hiệu giữa các ngày liên tiếp (số ngày)
     cycle_days = trung vị(các khoảng)   // trung vị chống nhiễu tốt hơn trung bình
     cycle_days = kẹp trong [7, 120]
  nếu purchases == 1:
     BỎ QUA (chưa đủ cơ sở đoán chu kỳ) — hoặc để mặc định 30 nếu muốn phủ rộng, nhưng
     bỏ qua thì danh sách sạch và ít nhắc sai hơn. Khuyến nghị: BỎ QUA.

  upsert vào kv_customer_reorder {
     customer_id, product_id,
     customer_name = tên từ map khách,
     phone         = contactNumber,
     product_name, last_purchase_date, cycle_days, purchases,
     updated_at = now()
  }
```

- **Trung vị chứ đừng trung bình**: một lần khách mua gộp 2 hộp làm khoảng cách dài bất thường,
  trung bình bị kéo lệch, trung vị thì không.
- **Kẹp [7,120]**: chặn chu kỳ vô lý (mua nhầm 2 lần trong ngày → 0 ngày; hoặc mua 1 lần cách nửa năm).
- Nên `delete` sạch bảng rồi `insert` lại mỗi lần sync (bảng nhỏ), hoặc `upsert` theo khoá chính.

## 3. Deploy — theo đúng kỷ luật đã ghi ở CLAUDE.md gốc

- **Deploy bằng CLI, KHÔNG qua MCP** `deploy_edge_function`:
  ```bash
  export SUPABASE_ACCESS_TOKEN="$SUPABASE_ACCESS_TOKEN_HDW"   # từ ~/.config/api-keys.env
  npx --yes supabase@latest functions deploy kiotviet-sync \
    --project-ref ltmlueqkajqmduoqghdf \
    --workdir /Users/Huy/Claude/App/HuongDienWork
  ```
- **Nghiệm thu bằng LỜI GỌI THẬT, đừng đọc dòng "Deployed Functions"** (nó in ra kể cả khi bản mới
  chưa phục vụ — bẫy đã ghi trong CLAUDE.md). Cách đo thật:
  1. Chạy sync: `curl -X POST .../functions/v1/kiotviet-sync -H 'apikey: <anon>' -d '{"days":180}'`
     → trả `{"ok":true,"counts":{...}}` có đếm số khách/nhóm đã ghi.
  2. Đọc lại REST đúng câu frontend gọi (mục 0) **kèm header `x-hd-key`** → phải ra vài dòng khách thật.
  3. Mở app → **Số liệu → Nhắc mua lại**: dòng trạng thái hiện *"Đang đọc lịch sử mua từ KiotViet (N khách)"*
     và có thẻ **KiotViet** ở từng khách.

## 4. Lưu ý an toàn / tài khoản

- Bảng chứa **tên + SĐT khách** → RLS phải kín như các bảng `kv_` khác (mục 1). Đừng test bằng cách
  tạm mở policy rồi quên đóng.
- Project Supabase `ltmlueqkajqmduoqghdf` **dùng chung** — đổi schema/secret ảnh hưởng cả phần Sales
  và chatbot. Chỉ THÊM bảng/nhánh mới, đừng sửa bảng `kv_` đang chạy.
- Nếu `chidoanbusiness@gmail.com` là tài khoản dùng chung với người thứ hai, cân nhắc trước khi tạo
  thêm secret/khoá mới ở đó (hoá đơn & quyền thu hồi nằm chung).

## 5. Ranh giới frontend ↔ backend (để không dẫm chân)

- Frontend **không tự gửi tin cho khách** — chỉ nhắc chủ shop + soạn tin để copy. Đây là chủ ý
  (app tĩnh, không server nền; Facebook siết việc shop nhắn trước). Backend **không cần** đụng gửi tin.
- Danh sách **nhập tay** (`hdw.reorder`) là của riêng frontend, đồng bộ qua mã sync. Backend chỉ lo
  bảng `kv_customer_reorder`. Hai nguồn hiển thị chung nhưng độc lập — khách trùng sẽ hiện 2 dòng
  (một "KiotViet", một "Nhập tay"), chấp nhận được ở bản đầu.
