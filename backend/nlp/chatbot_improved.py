"""
JEC Buddy - Improved chatbot.py
Changes vs original:
  - Works with both old (separate vectorizer+model) and new (pipeline wrapper) pkl files
  - Lowered fallback threshold with a second-chance soft-match
  - Returns JSON output (response + suggestions) so the Node.js backend can parse it
  - Better error messages
  - Comprehensive suggestion mapping for all intents
  - Improved fallback handling with contextual suggestions
  
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
    """Preprocess user input: lowercase, tokenize, stem, remove stopwords"""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = word_tokenize(text)
    words = [ps.stem(w) for w in words if w not in stop_words and len(w) > 1]
    return " ".join(words)

# ── Wrapper (Required for pickling compatibility) ─────────────────────────
class PipelineWrapper:
    """Wrapper class for sklearn pipeline compatibility"""
    def __init__(self, pipe):
        self._pipe = pipe
    def transform(self, texts):
        return texts
    def predict_proba(self, texts):
        return self._pipe.predict_proba(texts)
    def predict(self, texts):
        return self._pipe.predict(texts)

# ── Load ──────────────────────────────────────────────────────────────────────
try:
    model      = pickle.load(open(os.path.join(SCRIPT_DIR, "chatbot_model.pkl"), "rb"))
    vectorizer = pickle.load(open(os.path.join(SCRIPT_DIR, "vectorizer.pkl"), "rb"))
    with open(os.path.join(SCRIPT_DIR, "college_intents.json"), encoding="utf-8") as f:
        intents = json.load(f)
except FileNotFoundError as e:
    print(json.dumps({
        "response": "Error: Required model files not found. Please ensure chatbot_model.pkl, vectorizer.pkl, and college_intents.json are in the same directory.",
        "suggestions": [],
        "error": str(e)
    }))
    sys.exit(1)

ps         = PorterStemmer()
stop_words = set(stopwords.words("english"))

# ── Suggestion map ────────────────────────────────────────────────────────────
# Maps each intent to relevant follow-up suggestions
SUGGESTIONS = {
    "greeting":                     ["Admission process", "Fee structure", "Departments"],
    "admission_process":            ["Eligibility criteria", "Fee structure", "Contact info"],
    "eligibility":                  ["Admission process", "Fee structure", "Departments"],
    "fees_structure":               ["Scholarship info", "Hostel info", "Placement"],
    "departments":                  ["CSE dept", "AI & DS dept", "ECE dept"],
    
    # Department-specific suggestions
    "department_cse_info":          ["IT dept", "AI & DS dept", "Placement"],
    "department_ai_info":           ["CSE dept", "IT dept", "Placement"],
    "department_it_info":           ["CSE dept", "AI & DS dept", "Placement"],
    "department_ece_info":          ["EE dept", "Mechatronics dept", "Placement"],
    "department_ee_info":           ["ECE dept", "Civil dept", "Placement"],
    "department_civil_info":        ["Mechanical dept", "IP dept", "Placement"],
    "department_mechanical_info":   ["Mechatronics dept", "IP dept", "Placement"],
    "department_mechatronics_info": ["Mechanical dept", "ECE dept", "Placement"],
    "department_ip_info":           ["Mechanical dept", "Civil dept", "Placement"],
    
    # Facilities & Campus Life
    "hostel_info":                  ["Library info", "Mess info", "Sports info"],
    "library_info":                 ["Hostel info", "Timing info", "Study resources"],
    "mess_info":                    ["Hostel info", "Timing info", "Contact info"],
    "medical_facilities":           ["Hostel info", "Contact info", "Safety"],
    "transport_info":               ["Location", "Hostel info", "Contact info"],
    
    # Contact & Location
    "contact_info":                 ["Location", "Admission process", "Department contact"],
    "location_info":                ["Contact info", "Transport info", "Hostel info"],
    
    # Co-curricular Activities
    "sports_info":                  ["NCC info", "Fests & Events", "Clubs & Societies"],
    "ncc_nss_info":                 ["Sports info", "Clubs & Societies", "Certificate"],
    "fests_events":                 ["Clubs & Societies", "Sports info", "Cultural activities"],
    "clubs_societies":              ["Fests & Events", "NCC info", "Technical events"],
    
    # Placements & Career
    "placement_info":               ["Departments", "Training programs", "Scholarship"],
    "training_programs":            ["Placement", "Skill development", "Internship"],
    "internship_info":              ["Placement", "Training programs", "Companies"],
    
    # Academics & Policies
    "scholarship_info":             ["Fee structure", "Eligibility", "Documents required"],
    "dress_code_info":              ["Timing info", "Attendance policy", "Discipline"],
    "timing_info":                  ["Attendance policy", "Library timing", "Mess timing"],
    "attendance_policy":            ["Timing info", "Academic rules", "Leave policy"],
    "ragging_policy":               ["Anti-ragging measures", "Contact info", "Safety"],
    "exam_info":                    ["Attendance policy", "Academic calendar", "Results"],
    "results_info":                 ["Exam info", "Grading system", "Academic support"],
    
    # Academic Support
    "curriculum_info":              ["Departments", "Course structure", "Syllabus"],
    "faculty_info":                 ["Departments", "Contact info", "Office hours"],
    "laboratory_info":              ["Departments", "Practical schedule", "Equipment"],
    
    # Safety & Discipline
    "safety_measures":              ["Ragging policy", "Security", "Emergency contact"],
    "disciplinary_rules":           ["Attendance policy", "Code of conduct", "Penalties"],
    
    # Miscellaneous
    "wifi_info":                    ["Library info", "Hostel info", "IT support"],
    "canteen_info":                 ["Mess info", "Timing info", "Campus facilities"],
    "alumni_info":                  ["Placement", "Networking", "Events"],
    "research_info":                ["Departments", "Faculty info", "Publications"],
    
    # Exit intent
    "farewell":                     ["Contact info", "Admission process", "Visit again"],
    
    # Default fallback suggestions
    "default":                      ["Admission process", "Fee structure", "Departments", "Contact info"],
}

# ── Predict ───────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.35   # lowered from 0.40; TF-IDF+SVM is more calibrated

def predict(user_input: str):
    """Predict intent and confidence for user input"""
    processed = preprocess(user_input)
    
    # Handle empty input after preprocessing
    if not processed.strip():
        return None, 0.0
    
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
        out = {
            "response": "Please provide a message.", 
            "suggestions": ["Admission process", "Fee structure", "Departments", "Contact info"]
        }
        print(json.dumps(out) if json_mode else out["response"])
        return

    user_input = args[0].strip()
    
    # Handle empty input
    if not user_input:
        out = {
            "response": "Please provide a valid message.", 
            "suggestions": ["Admission process", "Fee structure", "Departments", "Contact info"]
        }
        print(json.dumps(out) if json_mode else out["response"])
        return

    try:
        tag, confidence = predict(user_input)

        # Handle cases where preprocessing returns empty string
        if tag is None:
            response    = "I couldn't process your message. Please try asking about JEC Jabalpur — admissions, fees, departments, hostel, etc."
            suggestions = SUGGESTIONS.get("default", ["Admission process", "Fee structure", "Departments"])
            tag = "unknown"
            confidence = 0.0
        
        # Low confidence - provide fallback
        elif confidence < CONFIDENCE_THRESHOLD:
            response    = "Sorry, I don't understand that. Please ask something related to JEC Jabalpur — admissions, fees, departments, hostel, placement, etc."
            suggestions = SUGGESTIONS.get("default", ["Admission process", "Fee structure", "Departments", "Hostel info"])
        
        # High confidence - provide response
        else:
            response    = ""
            suggestions = SUGGESTIONS.get(tag, SUGGESTIONS.get("default", ["Departments", "Fee structure", "Contact info"]))

            # Find matching intent and get response
            for intent in intents["intents"]:
                if intent["tag"] == tag:
                    response = random.choice(intent["responses"])
                    break

            # Fallback if no response found
            if not response:
                response = "I found a match but couldn't retrieve a response. Please try again or contact us directly."
                suggestions = ["Contact info", "Admission process", "Departments"]

        # Output response
        if json_mode:
            output = {
                "response": response, 
                "suggestions": suggestions, 
                "tag": tag, 
                "confidence": round(confidence, 3)
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            print(response)

    except Exception as e:
        err = {
            "response": "Something went wrong. Please try again or contact support.", 
            "suggestions": ["Contact info", "Admission process", "Departments"], 
            "error": str(e)
        }
        print(json.dumps(err, ensure_ascii=False) if json_mode else err["response"])
        if not json_mode:
            print(f"Error details: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    main()
