/**
 * apiService.js
 * Modular service for future LLM / External API integrations (OpenAI, Gemini, Groq, etc.)
 * Prepare for future integration by implementing callExternalAPI here.
 */

/**
 * Placeholder for future API integration.
 * @param {string} userMessage - The raw message from user.
 * @returns {Promise<{ response: string, source: string } | null>}
 */
const callExternalAPI = async (userMessage) => {
  // TODO: Integrate OpenAI, Groq, or another API here.
  // For now, it returns null to let the local NLP handle it.
  
  /* Example Implementation:
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', { ... });
    const data = await response.json();
    return { response: data.choices[0].message.content, source: 'openai' };
  } catch (err) {
    console.error("External API Error:", err);
    return null;
  }
  */
  
  return null; 
};

module.exports = { callExternalAPI };
