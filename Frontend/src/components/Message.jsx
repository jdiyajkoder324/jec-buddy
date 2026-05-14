const fmt = (iso) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export default function Message({ msg, onChipClick }) {
  const isUser = msg.role === "user";

  return (
    <div className={`msg-row ${isUser ? "user" : "bot"}`}>
      {!isUser && <div className="msg-avatar">🎓</div>}

      <div className="msg-bubble-wrap">
        <div className="msg-bubble" style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>
        <span className="msg-time">{fmt(msg.timestamp)}</span>

        {!isUser && msg.suggestions?.length > 0 && (
          <div className="suggestions">
            {msg.suggestions.map((s) => (
              <button key={s} className="chip" onClick={() => onChipClick(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
