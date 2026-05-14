const http = require("http");
const fs = require("fs");
const data = JSON.stringify({ message: "hi", sessionId: "user" });
const req = http.request(
  "http://127.0.0.1:5000/api/chat/message",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Content-Length": Buffer.byteLength(data),
    },
  },
  (res) => {
    let body = "";
    res.on("data", (c) => (body += c));
    res.on("end", () => fs.writeFileSync("test.log", "RES: " + body));
  }
);
req.on("error", (e) => fs.writeFileSync("test.log", "ERR: " + e.message));
req.write(data);
req.end();
