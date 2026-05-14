/**
 * chatController.js
 * Handles POST /message, GET /history/:sessionId, DELETE /history/:sessionId
 */

const { isConnected } = require("../config/db");
const Chat = require("../models/Chat");
const { getNLPResponse } = require("../services/nlpService");

// ── POST /api/chat/message ────────────────────────────────────────────────────
const sendMessage = async (req, res) => {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed." });
  }

  const { message, sessionId } = req.body;

  if (!message || typeof message !== "string" || !message.trim()) {
    return res.status(400).json({ error: "Message is required." });
  }
  if (!sessionId) {
    return res.status(400).json({ error: "sessionId is required." });
  }

  const userText = message.trim().slice(0, 500); // max 500 chars

  try {
    // 1. Get NLP/ML response
    const { response, suggestions, tag, confidence } = await getNLPResponse(userText);

    // 2. Persist to MongoDB (best-effort — don't fail request if DB is down)
    if (isConnected()) {
  try {
    let chat = await Chat.findOne({ sessionId });
    if (!chat) chat = new Chat({ sessionId, messages: [] });

    chat.messages.push({ role: "user", text: userText });
    chat.messages.push({ role: "bot", text: response, tag, confidence, suggestions });

    if (chat.messages.length > 200) {
      chat.messages = chat.messages.slice(-200);
    }

    await chat.save();
  } catch (dbErr) {
    console.warn("DB write skipped:", dbErr.message);
  }
}

    // 3. Return response to frontend
    return res.json({ response, suggestions, tag, confidence });

  } catch (err) {
    console.error("sendMessage error:", err);
    return res.status(500).json({
      error: "Internal server error.",
      response: "Something went wrong. Please try again.",
      suggestions: [],
    });
  }
};

// ── GET /api/chat/history/:sessionId ─────────────────────────────────────────
const getHistory = async (req, res) => {
  const { sessionId } = req.params;
  if (!sessionId) return res.status(400).json({ error: "sessionId required." });

  try {
    const chat = await Chat.findOne({ sessionId }).lean();
    if (!chat) return res.json({ sessionId, messages: [] });

    return res.json({ sessionId, messages: chat.messages });
  } catch (err) {
    console.error("getHistory error:", err);
    return res.status(500).json({ error: "Could not fetch history." });
  }
};

// ── DELETE /api/chat/history/:sessionId ──────────────────────────────────────
const deleteHistory = async (req, res) => {
  const { sessionId } = req.params;
  if (!sessionId) return res.status(400).json({ error: "sessionId required." });

  try {
    await Chat.deleteOne({ sessionId });
    return res.json({ message: "Chat history cleared.", sessionId });
  } catch (err) {
    console.error("deleteHistory error:", err);
    return res.status(500).json({ error: "Could not delete history." });
  }
};

// ── Export controller functions ───────────────────────────────────────────────
module.exports = {
  sendMessage,
  getHistory,
  deleteHistory
};