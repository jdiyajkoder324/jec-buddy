import React, { useState, useCallback, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import Header  from "./components/Header";
import ChatBox from "./components/ChatBox";
import InputBar from "./components/Input";
import "./styles/chat.css";

const API_BASE = "/api/chat";

// Persist session ID across page refreshes
const getSessionId = () => {
  let id = localStorage.getItem("jec_session");
  if (!id) { id = uuidv4(); localStorage.setItem("jec_session", id); }
  return id;
};

const makeMsg = (role, text, extras = {}) => ({
  id:          uuidv4(),
  role,
  text,
  timestamp:   new Date().toISOString(),
  suggestions: [],
  ...extras,
});

export default function App() {
  const [sessionId]            = useState(getSessionId);
  const [messages, setMessages] = useState([]);
  const [isTyping, setTyping]   = useState(false);

  // Load history on mount
  useEffect(() => {
    fetch(`${API_BASE}/history/${sessionId}`)
      .then((r) => r.json())
      .then(({ messages: hist }) => {
        if (hist?.length) {
          setMessages(
            hist.map((m) => ({
              id:          uuidv4(),
              role:        m.role,
              text:        m.text,
              timestamp:   m.createdAt || new Date().toISOString(),
              suggestions: m.suggestions || [],
            }))
          );
        }
      })
      .catch(() => {}); // silent fail — history is optional
  }, [sessionId]);

  const sendMessage = useCallback(async (text) => {
    // Optimistically add user message
    setMessages((prev) => [...prev, makeMsg("user", text)]);
    setTyping(true);

    try {
      const res = await fetch(`${API_BASE}/message`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ message: text, sessionId }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        makeMsg("bot", data.response  || "Sorry, I couldn't get a response.", {
          suggestions: data.suggestions || [],
        }),
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        makeMsg("bot", "⚠️ Could not reach the server. Please check your connection.", {
          suggestions: ["Admission process", "Fee structure", "Departments"],
        }),
      ]);
    } finally {
      setTyping(false);
    }
  }, [sessionId]);

  const handleClear = useCallback(async () => {
    setMessages([]);
    try {
      await fetch(`${API_BASE}/history/${sessionId}`, { method: "DELETE" });
    } catch {}
  }, [sessionId]);

  return (
    <div className="chat-root">
      <Header onClear={handleClear} isTyping={isTyping} />
      <ChatBox
        messages={messages}
        isTyping={isTyping}
        onChipClick={sendMessage}
      />
      <InputBar onSend={sendMessage} disabled={isTyping} />
    </div>
  );
}
