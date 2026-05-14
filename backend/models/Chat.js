const mongoose = require("mongoose");

// ── Individual message ────────────────────────────────────────────────────────
const MessageSchema = new mongoose.Schema(
  {
    role: {
      type: String,
      enum: ["user", "bot"],
      required: true,
    },
    text: {
      type: String,
      required: true,
      maxlength: 2000,
    },
    tag: String,           // intent tag (bot messages only)
    confidence: Number,    // ML confidence score (bot messages only)
    suggestions: [String], // quick-reply chips shown after this message
  },
  { timestamps: true }
);

// ── Chat session ──────────────────────────────────────────────────────────────
const ChatSchema = new mongoose.Schema(
  {
    sessionId: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    messages: [MessageSchema],
    lastActive: {
      type: Date,
      default: Date.now,
    },
  },
  { timestamps: true }
);

// Auto-update lastActive on save
ChatSchema.pre("save", function (next) {
  this.lastActive = new Date();
  next();
});

module.exports = mongoose.model("Chat", ChatSchema);
