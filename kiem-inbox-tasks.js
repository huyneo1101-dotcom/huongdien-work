// Kiểm 3 việc: (1) INBOX_TASKS còn cú pháp hợp lệ và có việc mới đủ 8 subtask,
// (2) fixDupIds vá được trùng id, (3) fixDupIds KHÔNG đụng bảng đã sạch (ca đối chứng).
const fs = require('fs');
const F = '/Users/Huy/Claude/App/HuongDienWork/index.html';
const s = fs.readFileSync(F, 'utf8');

// --- lấy nguyên khối INBOX_TASKS rồi eval ---
const i = s.indexOf('const INBOX_TASKS=[');
const j = s.indexOf('\n];', i);
const src = s.slice(i, j + 3).replace('const INBOX_TASKS=', 'module.exports.T=');
const m = { exports: {} };
new Function('module', src)(m);
const T = m.exports.T;

let hong = 0;
const ok = (ten, dieu) => { console.log((dieu ? '  ok  ' : '  HỎNG ') + ten); if (!dieu) hong++; };

ok('INBOX_TASKS parse được, ' + T.length + ' việc', T.length === 53);
const v = T.find(t => t.id === 'hd-2026-08-07-1');
ok('có việc mới hd-2026-08-07-1', !!v);
ok('việc mới pri=high, proj=mkt, due=2026-08-21',
   v && v.pri === 'high' && v.proj === 'mkt' && v.due === '2026-08-21');
ok('việc mới có 8 subtask, tất cả done=false',
   v && v.checklist.length === 8 && v.checklist.every(c => c.done === false && typeof c.t === 'string'));
ok('nhắc rào Nghị định 100/2014 trong ghi chú', v && v.note.includes('100/2014'));
ok('nêu đủ 3 mốc 23 / 41 / 80',
   v && ['23%', '41%', '80%'].every(x => v.note.includes(x)));

// --- lấy fixDupIds ra khỏi file ---
const a = s.indexOf('function fixDupIds(');
const b = s.indexOf('\n/* ---------- Kế hoạch phòng thủ', a);
const fixDupIds = new Function('return ' + s.slice(a, b))();

// CA PHẢI CHẶN: bảng có trùng id thì phải được tách ra
const dup = [{ id: 'x', title: 'A' }, { id: 'y', title: 'B' }, { id: 'x', title: 'C' }, { id: 'x', title: 'D' }];
const r = fixDupIds(dup);
ok('trùng id được tách: id duy nhất sau khi vá', new Set(r.map(t => t.id)).size === 4);
ok('bản gặp trước giữ nguyên id, bản sau thành x-b / x-c',
   r[0].id === 'x' && r[2].id === 'x-b' && r[3].id === 'x-c');
ok('nội dung từng việc không bị đổi', r.map(t => t.title).join('') === 'ABCD');

// CA ĐỐI CHỨNG: bảng sạch thì trả về ĐÚNG mảng cũ, không sinh mảng mới
const sach = [{ id: 'p' }, { id: 'q' }];
ok('bảng sạch: trả nguyên mảng cũ, không đụng gì', fixDupIds(sach) === sach);
// idempotent: chạy lại trên kết quả đã vá thì không đổi nữa
ok('chạy lần hai không đổi thêm (idempotent)', fixDupIds(r) === r);

// --- 6 cặp trùng thật trong file có được vá không ---
const ids = T.map(t => t.id);
const trung = ids.filter((x, k) => ids.indexOf(x) !== k);
console.log('  (6 id trùng thật trong file: ' + trung.join(', ') + ')');
const vaThat = fixDupIds(T.map(t => ({ id: t.id, title: t.title })));
ok('6 cặp trùng thật được tách hết', new Set(vaThat.map(t => t.id)).size === T.length);

console.log(hong ? '\nTRƯỢT ' + hong + ' ca' : '\nĐẠT toàn bộ ' + 12 + ' ca');
process.exit(hong ? 1 : 0);
