const API_URL = "https://jec-buddy.onrender.com/api/chat";

export const sendMessage = async (message, sessionId) => {
  const res = await fetch(`${API_URL}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, sessionId }),
  });
  return res.json();
};

export const getHistory = async (sessionId) => {
  const res = await fetch(`${API_URL}/history/${sessionId}`);
  return res.json();
};

export const deleteHistory = async (sessionId) => {
  const res = await fetch(`${API_URL}/history/${sessionId}`, {
    method: "DELETE",
  });
  return res.json();
};