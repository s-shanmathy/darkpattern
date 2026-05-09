import torch
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from transformers import AutoTokenizer, AutoModelForSequenceClassification

app = FastAPI()

# Allow CORS for the Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Device ────────────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# ── Load DistilRoBERTa Model ──────────────────────────────────────────────────
# The path must be relative to where the server is run. We'll run it from D:\SEM6\DL\DARK
# but to be safe, we'll use an absolute path or a path relative to the script's parent dir.
model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "distilroberta_darkpattern_detection")

print(f"Loading model from: {model_dir}")
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
model.eval()
print("DistilRoBERTa model loaded.")

# ── Tuning knobs ─────────────────────────────────────────────────────────────
# Only flag a text as a dark pattern if the model's confidence exceeds this.
# Increase this value (towards 1.0) to reduce false positives.
CONFIDENCE_THRESHOLD = 0.80

# Ignore text nodes shorter than this (likely labels, single words, etc.)
MIN_TEXT_LENGTH = 15

# ── Rule-Based Overrides (Hybrid Approach) ──────────────────────────────────
# Force specific text to be classified as NOT dark pattern (fixes false positives)
SAFE_OVERRIDE_KEYWORDS = [
    "secure checkout",
    "access all basic features",
    "standard plan",
    "maybe later"
]

# Force specific text to be classified as Dark Pattern (fixes false negatives)
DARK_OVERRIDE_KEYWORDS = [
    "highly recommended",  # usually associated with pre-ticked hidden insurance
    "pay full price and keep my life boring", # confirmshaming
    "maintenance fee"
]

class AnalyzeRequest(BaseModel):
    texts: List[str]

class AnalyzeResponseItem(BaseModel):
    text: str
    label: int
    label_name: str
    confidence: float

class AnalyzeResponse(BaseModel):
    results: List[AnalyzeResponseItem]

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    results = []
    if not request.texts:
        return AnalyzeResponse(results=results)

    # Process in batches for better performance if there are many texts
    batch_size = 16
    for i in range(0, len(request.texts), batch_size):
        batch_texts = request.texts[i:i+batch_size]
        
        # Filter out empty or very short strings to save computation
        valid_texts = [text for text in batch_texts if text and len(text.strip()) >= MIN_TEXT_LENGTH]
        if not valid_texts:
            continue

        with torch.no_grad():
            inputs = tokenizer(
                valid_texts,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256
            ).to(device)
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)
            
            for j, prob in enumerate(probs):
                current_text = valid_texts[j]
                current_text_lower = current_text.lower()
                
                # Apply Rules first
                is_safe_override = any(kw in current_text_lower for kw in SAFE_OVERRIDE_KEYWORDS)
                is_dark_override = any(kw in current_text_lower for kw in DARK_OVERRIDE_KEYWORDS)
                
                # Get confidence for the dark pattern class (index 1) specifically
                dark_confidence = prob[1].item()
                
                if is_safe_override:
                    label = 0
                    confidence = 1.0  # Absolute certainty based on rule
                elif is_dark_override:
                    label = 1
                    confidence = 1.0  # Absolute certainty based on rule
                elif dark_confidence >= CONFIDENCE_THRESHOLD:
                    # Fallback to model if no rule applies
                    label = 1
                    confidence = dark_confidence
                else:
                    label = 0
                    confidence = prob[0].item()

                results.append(AnalyzeResponseItem(
                    text=current_text,
                    label=label,
                    label_name="Dark Pattern" if label == 1 else "Not Dark Pattern",
                    confidence=confidence
                ))

    return AnalyzeResponse(results=results)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Dark Pattern Analysis API is running."}
