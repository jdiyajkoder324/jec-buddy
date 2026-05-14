require("dotenv").config();

const express = require("express");
const cors = require("cors");
const {connectDB} = require("./config/db");
const chatRoutes = require("./routes/chatRoutes");
const path       = require("path");
const fs         = require("fs");

const app = express();
const PORT = process.env.PORT || 5000;

// ── Database ─────────────────────────────────────────────────
connectDB();

// ── CORS ─────────────────────────────────────────────────────
const allowedOrigins = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(",").map((o) => o.trim())
  : ["http://localhost:5173", "http://localhost:5178", "http://127.0.0.1:5173", "http://127.0.0.1:5178"];

app.use(
  cors({
    origin: function (origin, callback) { callback(null, true); },
    methods: ["GET", "POST", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type"],
    credentials: true
  })
);

// ── Middleware ───────────────────────────────────────────────
app.use(express.json({ limit: "10kb" }));
app.use(express.urlencoded({ extended: false }));

// ── Routes ───────────────────────────────────────────────────
app.use("/api/chat", chatRoutes);

console.log("Routes Loaded");

// Root Route (Add this for testing)

// Health check
app.get("/health", (_req, res) =>
  res.json({ status: "ok", timestamp: new Date() })
);
app.get("/", (req, res) => {
  res.send("🚀 JEC Buddy Backend Running");
});

// GET /api/intents — return available intent tags
app.get("/api/intents", (req, res) => {
  try {
    const intentPath = path.join(__dirname, "nlp", "college_intents.json");
    if (!fs.existsSync(intentPath)) return res.status(404).json({ error: "Intents not found." });
    
    const data = JSON.parse(fs.readFileSync(intentPath, "utf-8"));
    const tags = data.intents.map(i => i.tag);
    res.json({ tags });
  } catch (err) {
    res.status(500).json({ error: "Error reading intents." });
  }
});

// 404 handler
app.use((_req, res) =>
  res.status(404).json({ error: "Route not found." })
);

// Global error handler
app.use((err, _req, res, _next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal server error." });
});

// ── Start ────────────────────────────────────────────────────
app.listen(PORT, "127.0.0.1", () => {
  console.log(`\n🚀 JEC Buddy backend running on http://127.0.0.1:${PORT}`);
  console.log(`POST   /api/chat/message`);
  console.log(`GET    /api/chat/history/:sessionId`);
  console.log(`DELETE /api/chat/history/:sessionId\n`);
});