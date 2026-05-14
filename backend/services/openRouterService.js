const axios = require("axios");

const getOpenRouterResponse = async (message) => {
  try {
    const response = await axios.post(
      process.env.OPENROUTER_API_URL,
      {
        model: "orca-mini-v2",
        messages: [{ role: "user", content: message }]
      },
      {
        headers: {
          "Authorization": `Bearer ${process.env.OPENROUTER_API_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    return response.data.choices[0].message.content;

  } catch (error) {
    console.error("OpenRouter Error:", error.message);
    return null;
  }
};

module.exports = getOpenRouterResponse;