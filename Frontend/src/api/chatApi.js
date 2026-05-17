const API = "https://jec-buddy.onrender.com/api/chat";

export const sendMessage = async (message, sessionId) => {
  const res = await fetch(`${API}/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message,
      sessionId
    })
  });

  return res.json();
};