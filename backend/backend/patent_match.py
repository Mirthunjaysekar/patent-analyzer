# patent_match.py
from sentence_transformers import SentenceTransformer, util

# Load sentence transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Example user input (replace later with frontend input)
user_idea = """
Smart glasses for visually impaired users with object recognition, 
real-time scene description, navigation assistance, and voice feedback system.
"""

# Example related patents (normally will come from Google Patents API or scraping)
related_patents = [
    {
        "title": "Spectacle frame capable of being inserted with eyeglasses",
        "snippet": "A spectacle frame design with grooves for inserting custom lenses."
    },
    {
        "title": "Lens fixing method for rimless eyeglasses",
        "snippet": "A technique for fixing lenses to rimless eyeglass frames."
    },
    {
        "title": "Combined multipurpose glasses",
        "snippet": "Glasses with polarized lenses, sunshade, and light variation meeting lenses."
    },
    {
        "title": "AI-based wearable smart glasses",
        "snippet": "Smart glasses with AI that provide object detection and navigation features."
    }
]

# STEP 1: Break down user idea into feature chunks
features = [
    "Object recognition",
    "Real-time scene description",
    "Navigation assistance",
    "Voice feedback system"
]

# STEP 2: Encode features and patent descriptions
feature_embeddings = model.encode(features, convert_to_tensor=True)
patent_texts = [patent["title"] + " " + patent["snippet"] for patent in related_patents]
patent_embeddings = model.encode(patent_texts, convert_to_tensor=True)

# STEP 3: Match each feature with patents
threshold = 0.55  # similarity threshold (tune this if needed)

delta_results = []
for i, feature in enumerate(features):
    similarities = util.pytorch_cos_sim(feature_embeddings[i], patent_embeddings)[0]
    best_match_idx = int(similarities.argmax())
    best_score = float(similarities[best_match_idx])

    if best_score >= threshold:
        delta_results.append({
            "feature": feature,
            "status": "✅ Already present in patents",
            "matched_patent": related_patents[best_match_idx]["title"],
            "similarity": round(best_score, 3)
        })
    else:
        delta_results.append({
            "feature": feature,
            "status": "❌ Novel / Not found in patents",
            "matched_patent": None,
            "similarity": round(best_score, 3)
        })

# STEP 4: Print Delta Logic Report
print("\n🔎 Delta Logic Report\n")
print(f"User Idea: {user_idea}\n")

for res in delta_results:
    print(f"- {res['feature']}: {res['status']}")
    if res["matched_patent"]:
        print(f"   ↳ Similar Patent: {res['matched_patent']} (Score: {res['similarity']})")
    else:
        print(f"   ↳ No close patent found (Score: {res['similarity']})")

