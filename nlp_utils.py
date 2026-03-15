import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import datetime

# Simple category mapping for simulation
CATEGORY_KEYWORDS = {
    "Electricity": ["light", "street light", "currentcut", "power", "current", "wire", "shock", "voltage", "meter", "eb", "transformer", "fuse", "blackout"],
    "Water": ["overflow", "pipelineclot", "no water", "tap issue", "leak", "pipe", "drinking", "tanker", "contamination", "low pressure"],
    "Roads": ["way damage", "road", "pothole", "tar", "speed", "breaker", "accident", "path", "bridge", "street", "crack", "block", "divider"],
    "Sanitation": ["septitank", "overflow", "smell", "drainage overflow", "septitank smell", "garbage", "waste", "trash", "cleaning", "bins", "stinking", "litter", "dump", "sweep", "drain", "stagnant"]
}

PRIORITY_KEYWORDS = {
    "High": ["danger", "leakage", "fire", "overflow", "urgent", "emergency", "critical"],
    "Medium": ["damage", "broken", "pothole", "stuck", "problem"],
    "Low": ["slow", "delay", "request", "minor", "suggestion", "feedback"]
}

def classify_complaint(description):
    desc = description.lower()
    
    # NLP Category Classification
    detected_category = "General"
    max_matches = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in desc)
        if matches > max_matches:
            max_matches = matches
            detected_category = cat
            
    # Priority Classification
    detected_priority = "Low"
    for p, keywords in PRIORITY_KEYWORDS.items():
        if any(kw in desc for kw in keywords):
            detected_priority = p
            break
    
    # Deadline Calculation based on priority
    # High: 24h, Medium: 48h, Low: 72h
    hours = 24 if detected_priority == "High" else 48 if detected_priority == "Medium" else 72
    deadline = datetime.datetime.now() + datetime.timedelta(hours=hours)
    
    return detected_category, detected_priority, deadline

def detect_duplicate(new_desc, existing_complaints):
    if not existing_complaints:
        return False, None
    
    descriptions = [c['description'] for c in existing_complaints]
    all_texts = descriptions + [new_desc]
    
    vectorizer = TfidfVectorizer().fit_transform(all_texts)
    vectors = vectorizer.toarray()
    
    # Compare the last vector (new_desc) with all others
    similarities = cosine_similarity([vectors[-1]], vectors[:-1])[0]
    
    max_sim = np.max(similarities) if len(similarities) > 0 else 0
    if max_sim > 0.8:  # 80% similarity threshold
        idx = np.argmax(similarities)
        return True, existing_complaints[idx]
    
    return False, None
