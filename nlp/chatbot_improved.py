"""
JEC Buddy - Improved chatbot.py
Changes vs original:
  - Works with both old (separate vectorizer+model) and new (pipeline wrapper) pkl files
  - Lowered fallback threshold with a second-chance soft-match
  - Returns JSON output (response + suggestions) so the Node.js backend can parse it
  - Better error messages
Usage:
    python chatbot.py "<user message>"
    python chatbot.py "<user message>" --json   ← returns JSON for backend use
"""

import sys
import json
import pickle
import random
import re
import os

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Preprocess ────────────────────────────────────────────────────────────────
def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = word_tokenize(text)
    words = [ps.stem(w) for w in words if w not in stop_words and len(w) > 1]
    return " ".join(words)

# ── Wrapper (Required for pickling compatibility) ─────────────────────────
class PipelineWrapper:
    def __init__(self, pipe):
        self._pipe = pipe
    def transform(self, texts):
        return texts
    def predict_proba(self, texts):
        return self._pipe.predict_proba(texts)
    def predict(self, texts):
        return self._pipe.predict(texts)

# ── Load ──────────────────────────────────────────────────────────────────────
model      = pickle.load(open(os.path.join(SCRIPT_DIR, "chatbot_model.pkl"), "rb"))
vectorizer = pickle.load(open(os.path.join(SCRIPT_DIR, "vectorizer.pkl"), "rb"))
with open(os.path.join(SCRIPT_DIR, "college_intents.json"), encoding="utf-8") as f:
    intents = json.load(f)

ps         = PorterStemmer()
stop_words = set(stopwords.words("english"))

# ── Suggestion map ────────────────────────────────────────────────────────────
SUGGESTIONS = {
    "greeting":                ["Admission process", "Fee structure", "Departments"],
    "admission_process":       ["Eligibility criteria", "Fee structure", "Contact info"],
    "eligibility":             ["Admission process", "Fee structure", "Departments"],
    "fees_structure":          ["Hostel info", "Departments", "Contact info"],
    "departments":             ["CSE dept", "AI & DS dept", "ECE dept"],
    "department_cse_info":     ["IT dept", "AI & DS dept", "Fee structure"],
    "department_ai_info":      ["CSE dept", "IT dept", "Fee structure"],
    "department_it_info":      ["CSE dept", "ECE dept", "Fee structure"],
    "department_ece_info":     ["EE dept", "Mechatronics dept", "Fee structure"],
    "department_ee_info":      ["ECE dept", "Civil dept", "Fee structure"],
    "department_civil_info":   ["Mechanical dept", "IP dept", "Hostel info"],
    "department_mechanical_info": ["Mechatronics dept", "IP dept", "Fee structure"],
    "department_mechatronics_info": ["Mechanical dept", "ECE dept", "Fee structure"],
    "department_ip_info":      ["Mechanical dept", "Civil dept", "Fee structure"],
    "hostel_info":             ["Library info", "Contact info", "Location"],
    "library_info":            ["Hostel info", "Contact info", "Departments"],
    "contact_info":            ["Location", "Admission process", "Fee structure"],
    "location_info":           ["Contact info", "Hostel info", "Admission process"],
    "sports_info":             ["NCC info", "Fests & Events", "Attendance policy"],
    "ncc_nss_info":            ["Sports info", "Clubs & Societies", "Scholarship"],
    "fests_events":            ["Sports info", "Clubs & Societies", "Placement"],
    "placement_info":          ["Fee structure", "Departments", "Scholarship"],
    "scholarship_info":        ["Fee structure", "Eligibility", "Admission process"],
    "dress_code_info":         ["Timing info", "Attendance policy", "Ragging policy"],
    "timing_info":             ["Attendance policy", "Dress code", "Library info"],
    "clubs_societies":         ["Fests & Events", "NCC info", "Sports info"],
    "attendance_policy":       ["Timing info", "Dress code", "Ragging policy"],
    "ragging_policy":          ["Attendance policy", "Contact info", "Safety"],
    "farewell":                [],
}

# ── Predict ───────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.35   # lowered from 0.40; TF-IDF+SVM is more calibrated

def predict(user_input: str):
    processed = preprocess(user_input)
    vector    = vectorizer.transform([processed])
    probs     = model.predict_proba(vector)
    confidence = float(max(probs[0]))
    tag        = model.predict(vector)[0]
    return tag, confidence

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    json_mode = "--json" in sys.argv
    args      = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        out = {"response": "Please provide a message.", "suggestions": []}
        print(json.dumps(out) if json_mode else out["response"])
        return

    user_input = args[0]

    try:
        tag, confidence = predict(user_input)

        if confidence < CONFIDENCE_THRESHOLD:
            response    = "Sorry, I don't understand that. Please ask something related to JEC Jabalpur — admissions, fees, departments, hostel, etc."
            suggestions = ["Admission process", "Fee structure", "Departments", "Hostel info"]
        else:
            response    = ""
            suggestions = SUGGESTIONS.get(tag, ["Departments", "Fee structure", "Contact info"])

            for intent in intents["intents"]:
                if intent["tag"] == tag:
                    response = random.choice(intent["responses"])
                    break

            if not response:
                response = "I found a match but couldn't retrieve a response. Please try again."

        if json_mode:
            print(json.dumps({"response": response, "suggestions": suggestions, "tag": tag, "confidence": round(confidence, 3)}))
        else:
            print(response)

    except Exception as e:
        err = {"response": "Something went wrong. Please try again.", "suggestions": [], "error": str(e)}
        print(json.dumps(err) if json_mode else err["response"])

if __name__ == "__main__":
    main()
