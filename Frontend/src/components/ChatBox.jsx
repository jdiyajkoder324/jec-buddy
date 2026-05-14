import { useEffect, useRef } from "react";
import Message from "./Message";

const WELCOME_CHIPS = [
  "Admission process", "Fee structure", "Departments",
  "Sports & NCC", "Placements", "College Fests",
];

export default function ChatBox({ messages, isTyping, onChipClick }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (messages.length === 0) {
    return (
      <div className="chat-messages">
        <div className="welcome">
          <div className="welcome-icon">🎓</div>
          <h2>Hey there! I'm JEC Buddy</h2>
          <p>Ask me anything about Jabalpur Engineering College — admissions, fees, departments, hostel, and more.</p>
          <div className="welcome-chips">
            {WELCOME_CHIPS.map((c) => (
              <button key={c} className="chip" onClick={() => onChipClick(c)}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-messages">
      {messages.map((msg) => (
        <Message key={msg.id} msg={msg} onChipClick={onChipClick} />
      ))}

      {isTyping && (
        <div className="typing-row">
          <div className="msg-avatar">🎓</div>
          <div className="typing-bubble">
            <span /><span /><span />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
