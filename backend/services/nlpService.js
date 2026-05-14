const { spawn } = require("child_process");
const path = require("path");
const fs   = require("fs");
const getOpenRouterResponse = require("./openRouterService");

const PYTHON_PATH  = process.env.PYTHON_PATH  || "python";
const CHATBOT_DIR = process.env.CHATBOT_DIR
  ? path.resolve(process.env.CHATBOT_DIR)
  : path.join(__dirname, "../../nlp");

const script = fs.existsSync(path.join(CHATBOT_DIR, "chatbot_improved.py"))
  ? path.join(CHATBOT_DIR, "chatbot_improved.py")
  : path.join(CHATBOT_DIR, "chatbot.py");

const TIMEOUT_MS = 10_000;

const fallbackResponse = (reason) => ({
  response:    `Sorry, I'm having trouble right now. ${reason} Please try again.`,
  suggestions: ["Admission process", "Fee structure", "Departments", "Sports & NCC", "Placements", "College Fests"],
  tag:         "error",
  confidence:  0,
});

const getNLPResponse = async (message) => {
  const pythonResp = await new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let settled = false;

    const proc = spawn(PYTHON_PATH, [script, message, "--json"], {
      cwd: CHATBOT_DIR,
    });

    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        proc.kill();
        resolve(fallbackResponse("Request timed out."));
      }
    }, TIMEOUT_MS);

    proc.stdout.on("data", (d) => (stdout += d.toString()));
    proc.stderr.on("data", (d) => (stderr += d.toString()));

    proc.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);

      if (code !== 0 || !stdout.trim()) {
        console.error("Python error:", stderr);
        resolve(fallbackResponse("The AI engine encountered an error."));
        return;
      }

      try {
        const parsed = JSON.parse(stdout.trim());
        resolve({
          response:    parsed.response    || "No response.",
          suggestions: parsed.suggestions || [],
          tag:         parsed.tag         || "unknown",
          confidence:  parsed.confidence  ?? 0,
        });
      } catch {
        resolve({
          response:    stdout.trim(),
          suggestions: ["Admission process", "Fee structure", "Departments"],
          tag:         "unknown",
          confidence:  1,
        });
      }
    });

    proc.on("error", (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      console.error("Spawn error:", err.message);
      resolve(fallbackResponse("Could not start AI engine."));
    });
  });

  // OpenRouter fallback if Python confidence < 0.6
  if (pythonResp.confidence < 0.6) {
    try {
      const aiReply = await getOpenRouterResponse(message);
      if (aiReply) return aiReply;
    } catch (err) {
      console.error("OpenRouter fallback error:", err.message);
    }
  }

  return pythonResp;
};

module.exports = { getNLPResponse };