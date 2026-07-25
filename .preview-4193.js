// Static server tạm (verify) — có thể xoá an toàn.
const http = require("http"), fs = require("fs"), path = require("path");
const root = __dirname, port = 4193;
const types = {
  ".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8",
  ".css":"text/css; charset=utf-8", ".json":"application/json", ".svg":"image/svg+xml",
  ".png":"image/png", ".jpg":"image/jpeg", ".ico":"image/x-icon"
};
http.createServer((req, res) => {
  let p = decodeURIComponent((req.url || "/").split("?")[0]);
  if (p === "/") p = "/index.html";
  const fp = path.join(root, p);
  fs.readFile(fp, (e, d) => {
    if (e) { res.writeHead(404); res.end("404"); return; }
    res.writeHead(200, { "content-type": types[path.extname(fp).toLowerCase()] || "application/octet-stream" });
    res.end(d);
  });
}).listen(port, () => console.log("verify on http://localhost:" + port));
