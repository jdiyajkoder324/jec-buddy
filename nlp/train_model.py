"""
JEC Buddy - Model Training Script (v2.0)
=========================================
Naye intents add hone ke baad is script se model dobara train karo.

Run karo:
    python train_model.py

Output:
    chatbot_model.pkl   ← ML model
    vectorizer.pkl      ← TF-IDF vectorizer
    training_report.txt ← Accuracy & class-wise report
"""

import json
import re
import os
import pickle
import nltk
import numpy as np

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
from collections import Counter

# ── NLTK downloads ────────────────────────────────────────────────────────────
print("📦 Downloading NLTK data...")
nltk.download("punkt",     quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
print("✅ NLTK ready\n")

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
INTENTS_FILE  = os.path.join(SCRIPT_DIR, "college_intents.json")
MODEL_OUT     = os.path.join(SCRIPT_DIR, "chatbot_model.pkl")
VECTOR_OUT    = os.path.join(SCRIPT_DIR, "vectorizer.pkl")
REPORT_OUT    = os.path.join(SCRIPT_DIR, "training_report.txt")

# ── NLP setup ─────────────────────────────────────────────────────────────────
ps         = PorterStemmer()
stop_words = set(stopwords.words("english"))

def preprocess(text: str) -> str:
    text  = text.lower()
    text  = re.sub(r"[^a-z0-9\s]", " ", text)
    words = word_tokenize(text)
    words = [ps.stem(w) for w in words if w not in stop_words and len(w) > 1]
    return " ".join(words)

# ── Load intents ──────────────────────────────────────────────────────────────
print(f"📂 Loading intents from: {INTENTS_FILE}")
if not os.path.exists(INTENTS_FILE):
    raise FileNotFoundError(f"❌ File not found: {INTENTS_FILE}")

with open(INTENTS_FILE, encoding="utf-8") as f:
    data = json.load(f)

# ── Build dataset ─────────────────────────────────────────────────────────────
X_raw, y = [], []

skipped_tags = []
for intent in data["intents"]:
    tag      = intent["tag"]
    patterns = intent.get("patterns", [])

    # Skip fallback (no patterns) and tags with too few patterns
    if tag == "fallback" or len(patterns) == 0:
        skipped_tags.append(tag)
        continue

    for pattern in patterns:
        X_raw.append(preprocess(pattern))
        y.append(tag)

print(f"\n📊 Dataset Summary:")
print(f"   Total training samples : {len(X_raw)}")
print(f"   Total classes (intents): {len(set(y))}")
if skipped_tags:
    print(f"   Skipped tags           : {skipped_tags}")

# Show class distribution
counts = Counter(y)
print(f"\n📋 Patterns per intent:")
for tag, count in sorted(counts.items(), key=lambda x: x[1]):
    bar = "█" * count
    warn = " ⚠️  (low — add more patterns!)" if count < 8 else ""
    print(f"   {tag:<40} {count:>3}  {bar}{warn}")

# ── Train ─────────────────────────────────────────────────────────────────────
print("\n🚀 Training TF-IDF + SVM model...")

vectorizer = TfidfVectorizer(
    ngram_range  = (1, 2),   # unigrams + bigrams
    max_features = 5000,
    sublinear_tf = True,     # log scaling — helps with imbalanced classes
)
X_vec = vectorizer.fit_transform(X_raw)

model = SVC(
    kernel      = "linear",
    probability = True,   # needed for predict_proba / confidence score
    C           = 2.0,    # tuned: best accuracy on this dataset
)
model.fit(X_vec, y)

# ── Evaluate ──────────────────────────────────────────────────────────────────
print("\n📈 Running 5-fold cross-validation...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X_vec, y, cv=cv, scoring="accuracy")

print(f"\n✅ Cross-Val Accuracy: {scores.mean()*100:.1f}% (+/- {scores.std()*100:.1f}%)")
print(f"   Per-fold scores: {[f'{s*100:.1f}%' for s in scores]}")

# Full classification report on training data
y_pred  = model.predict(X_vec)
report  = classification_report(y, y_pred, zero_division=0)

# ── Save report ───────────────────────────────────────────────────────────────
with open(REPORT_OUT, "w", encoding="utf-8") as f:
    f.write("JEC Buddy - Training Report\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Total samples  : {len(X_raw)}\n")
    f.write(f"Total intents  : {len(set(y))}\n")
    f.write(f"CV Accuracy    : {scores.mean()*100:.1f}% (+/- {scores.std()*100:.1f}%)\n\n")
    f.write("Classification Report (on training data):\n")
    f.write("-" * 60 + "\n")
    f.write(report)

print(f"\n📄 Report saved: {REPORT_OUT}")

# ── Save model & vectorizer ───────────────────────────────────────────────────
pickle.dump(model,      open(MODEL_OUT,  "wb"))
pickle.dump(vectorizer, open(VECTOR_OUT, "wb"))

print(f"💾 Model saved     : {MODEL_OUT}")
print(f"💾 Vectorizer saved: {VECTOR_OUT}")
print("\n🎉 Training complete! Ab chatbot_improved.py use karo.")
