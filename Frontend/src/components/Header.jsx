import React from "react";

export default function Header({ onClear, isTyping }) {
  return (
    <header className="chat-header">
      <div className="header-avatar">🎓</div>
      <div className="header-info">
        <h1>JEC Buddy</h1>
        <p className="subtitle">{isTyping ? "Bot is typing..." : "Jabalpur Engineering College · AI Guide"}</p>
      </div>
      <div className="status-dot" title="Online" />
      <button className="header-clear" onClick={onClear} title="Clear chat">
        Clear
      </button>
    </header>
  );
}
