"""
JEC Buddy - Improved Training Script
Upgrades:
  - TfidfVectorizer with bigrams (1,2) instead of plain CountVectorizer
  - LinearSVC (better for short-text classification) with Platt scaling for probabilities
  - GridSearchCV for hyperparameter tuning
  - Stratified cross-validation report
  - Saves both model + vectorizer as before (drop-in replacement)
"""

import json
import pickle
import warnings
import re

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report

warnings.filterwarnings("ignore")

# ── NLTK setup ──────────────────────────────────────────────────────────────
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)

ps = PorterStemmer()
stop_words = set(stopwords.words("english"))

# ── Preprocessing ────────────────────────────────────────────────────────────
def preprocess(text: str) -> str:
    """
    Lowercase → remove punctuation → tokenize → remove stopwords → stem.
    Works for both English and Hinglish patterns.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = word_tokenize(text)
    words = [ps.stem(w) for w in words if w not in stop_words and len(w) > 1]
    return " ".join(words)

# ── Load intents ─────────────────────────────────────────────────────────────
with open("college_intents.json", encoding="utf-8") as f:
    data = json.load(f)

patterns, tags = [], []
for intent in data["intents"]:
    for pattern in intent["patterns"]:
        patterns.append(preprocess(pattern))
        tags.append(intent["tag"])

print(f"Total training samples : {len(patterns)}")
print(f"Unique intent classes   : {len(set(tags))}")
print()

# ── Build pipeline ───────────────────────────────────────────────────────────
#   TfidfVectorizer  →  LinearSVC wrapped with Platt scaling (gives predict_proba)
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),          # unigrams + bigrams
        min_df=1,
        sublinear_tf=True,           # log(1+tf) dampens frequent terms
        analyzer="word",
    )),
    ("clf", CalibratedClassifierCV(
        LinearSVC(max_iter=2000, class_weight="balanced"),
        cv=2,
        method="sigmoid",            # Platt scaling → predict_proba
    )),
])

# ── GridSearch for best C ─────────────────────────────────────────────────────
param_grid = {
    "clf__estimator__C": [0.1, 0.5, 1.0, 5.0, 10.0],
    "tfidf__ngram_range": [(1, 1), (1, 2)],
}

print("Running GridSearchCV (this may take a moment)…")
skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

# Use simple cross_val if too few samples per class for grid search
min_samples_per_class = min(tags.count(t) for t in set(tags))
if min_samples_per_class >= 3:
    grid = GridSearchCV(pipeline, param_grid, cv=skf, scoring="accuracy", n_jobs=-1)
    grid.fit(patterns, tags)
    best_model = grid.best_estimator_
    print(f"Best params  : {grid.best_params_}")
    print(f"Best CV acc  : {grid.best_score_:.3f}")
else:
    print("Too few samples for GridSearch — fitting directly with best defaults.")
    best_model = pipeline
    best_model.fit(patterns, tags)

# ── Cross-validation report ───────────────────────────────────────────────────
print("\n── Stratified 3-Fold Cross-Validation ──────────────────────────────")
scores = cross_val_score(best_model, patterns, tags, cv=skf, scoring="accuracy")
print(f"Fold accuracies : {[round(s, 3) for s in scores]}")
print(f"Mean ± Std      : {scores.mean():.3f} ± {scores.std():.3f}")

# ── Final fit + classification report ────────────────────────────────────────
best_model.fit(patterns, tags)
y_pred = best_model.predict(patterns)
print("\n── Per-class Report (training set) ─────────────────────────────────")
print(classification_report(tags, y_pred, zero_division=0))

# ── Save ──────────────────────────────────────────────────────────────────────
# Save the full pipeline as "model" so chatbot.py works unchanged.
# The vectorizer step is embedded inside the pipeline, so we also export
# a thin wrapper that mimics the old separate (vectorizer, model) API.

class PipelineWrapper:
    """
    Wraps the sklearn Pipeline so existing chatbot.py code that calls
        vector = vectorizer.transform([text])
        probs  = model.predict_proba(vector)
        tag    = model.predict(vector)[0]
    still works without any changes.
    """
    def __init__(self, pipe):
        self._pipe = pipe

    # --- vectorizer-like API ---
    def transform(self, texts):
        # Return texts as-is; the model's predict* handles them directly
        return texts

    # --- model-like API ---
    def predict_proba(self, texts):
        return self._pipe.predict_proba(texts)

    def predict(self, texts):
        return self._pipe.predict(texts)


wrapper = PipelineWrapper(best_model)

with open("chatbot_model.pkl", "wb") as f:
    pickle.dump(wrapper, f)

# vectorizer.pkl is now a passthrough; keep for compatibility
with open("vectorizer.pkl", "wb") as f:
    pickle.dump(wrapper, f)

print("\n✅ Model and vectorizer saved (drop-in replacement for old files).")
print("   chatbot.py requires NO changes — just re-run it.")
