import json
import re
import requests

def analyze_raw_text(doc_id, text, api_key):
    """
    Analyzes raw feedback text using Mistral Large and returns a structured JSON dictionary of insights.
    
    Args:
        doc_id (int/str): The ID of the document.
        text (str): The raw text extracted from OCR.
        api_key (str): The Mistral API key.
        
    Returns:
        dict: The structured analysis result.
    """
    if not api_key:
        raise ValueError("Mistral API key is required.")
        
    if not text.strip():
        # Fallback for empty text
        return {
            "document_id": doc_id,
            "summary": "Le document ne contient pas de texte lisible à analyser.",
            "overall_sentiment": "Neutral",
            "sentiment_score": 5.0,
            "strengths": [],
            "improvement_areas": ["Aucun texte n'a pu être extrait par l'OCR"],
            "themes": ["Aucun"],
            "representative_quotes": [],
            "recommended_actions": []
        }
        
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are an expert HR analyst specialized in analyzing employee feedback forms.
Analyze the following raw feedback text extracted via OCR.

TEXT TO ANALYZE:
---
{text}
---

Your task is to extract high-quality, actionable HR insights and return them in a STRICT JSON format.

RULES FOR EXTRACTION:
1. "document_id": Set this to the string value "{doc_id}".
2. "summary": Provide a concise 2-3 sentence overview of the employee's feedback.
3. "overall_sentiment": Classify the global tone as exactly one of: "Positive", "Neutral", or "Negative".
4. "sentiment_score": Grade the sentiment score on a scale from 1 (highly dissatisfied/negative) to 10 (highly satisfied/positive).
5. "strengths": A JSON array of specific strengths, achievements, or positive comments mentioned (e.g. "Excellent guidance from the supervisor during onboarding"). DO NOT list single words.
6. "improvement_areas": A JSON array of specific pain points, criticisms, or challenges mentioned (e.g. "Workload is too high during end-of-month reporting cycles"). DO NOT list single words.
7. "themes": A JSON array of general themes/topics discussed in this feedback (e.g. ["Supervisor Guidance", "Workload", "Communication", "Training"]).
8. "representative_quotes": A JSON array of direct or paraphrased key quotes from the text representing the employee's core points.
9. "recommended_actions": A JSON array of specific, actionable HR recommendations to address the feedback.

CRITICAL RULES:
- Output MUST be a single JSON object.
- Do NOT wrap the JSON in Markdown code fences (like ```json).
- Do NOT output any conversational text or explanations before or after the JSON.
- For list arrays (strengths, improvement_areas, quotes, actions), use full, meaningful phrases or sentences, not single words.
"""

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise RuntimeError(f"Mistral Chat Request failed (HTTP {response.status_code}): {response.text}")
        
    res_content = response.json()["choices"][0]["message"]["content"]
    
    return parse_json_insights(res_content, doc_id)

def parse_json_insights(content, doc_id):
    """Safely cleans and parses JSON content from the API."""
    cleaned = content.strip()
    
    # Strip markdown code fences if outputted
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        
    try:
        data = json.loads(cleaned)
        # Force format schema validation/alignment
        result = {
            "document_id": doc_id,
            "summary": str(data.get("summary", "")),
            "overall_sentiment": str(data.get("overall_sentiment", "Neutral")),
            "sentiment_score": float(data.get("sentiment_score", 5.0)),
            "strengths": list(data.get("strengths", [])),
            "improvement_areas": list(data.get("improvement_areas", [])),
            "themes": list(data.get("themes", [])),
            "representative_quotes": list(data.get("representative_quotes", [])),
            "recommended_actions": list(data.get("recommended_actions", []))
        }
        return result
    except Exception as e:
        # Fallback default dict
        return {
            "document_id": doc_id,
            "summary": f"Erreur de parsing de l'analyse (Brut: {cleaned[:100]}...)",
            "overall_sentiment": "Neutral",
            "sentiment_score": 5.0,
            "strengths": [],
            "improvement_areas": [f"Erreur d'analyse: {str(e)}"],
            "themes": ["Erreur de Parsing"],
            "representative_quotes": [],
            "recommended_actions": []
        }
