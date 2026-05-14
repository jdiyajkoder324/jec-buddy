const express = require("express");
const router  = express.Router();
const { sendMessage,
  getHistory,
  deleteHistory} = require("../controllers/chatController");

// POST   /api/chat/message          — send a message, get bot response
router.post("/message", sendMessage);

// GET    /api/chat/history/:sessionId — fetch past messages for a session
router.get("/history/:sessionId", getHistory);

// DELETE /api/chat/history/:sessionId — clear chat history for a session
router.delete("/history/:sessionId", deleteHistory);

module.exports = router;
