import json
import requests

def generate_executive_report(aggregation_data, api_key):
    """
    Generates a comprehensive executive HR report using Mistral Large, based on aggregated feedback data.
    
    Args:
        aggregation_data (dict): Output from aggregation.compute_aggregation().
        api_key (str): The Mistral API key.
        
    Returns:
        str: A markdown-formatted executive report.
    """
    if not api_key:
        raise ValueError("Mistral API key is required.")
    
    total = aggregation_data.get("total_count", 0)
    if total == 0:
        return "# Rapport Exécutif RH\n\nAucun feedback n'a encore été analysé. Veuillez télécharger et traiter des formulaires de feedback avant de générer un rapport."
    
    sentiment_dist = aggregation_data.get("sentiment_distribution", {})
    avg_score = aggregation_data.get("average_score", 5.0)
    theme_counts = aggregation_data.get("theme_counts", [])
    all_strengths = aggregation_data.get("all_strengths", [])
    all_issues = aggregation_data.get("all_improvement_areas", [])
    all_quotes = aggregation_data.get("all_quotes", [])
    
    # Build a structured data summary for the LLM
    data_summary = f"""
AGGREGATED HR FEEDBACK DATA:
- Total documents analyzed: {total}
- Sentiment distribution: Positive={sentiment_dist.get('Positive', 0)}, Neutral={sentiment_dist.get('Neutral', 0)}, Negative={sentiment_dist.get('Negative', 0)}
- Average sentiment score (1-10): {avg_score}

TOP THEMES (ranked by frequency):
{json.dumps(theme_counts[:15], ensure_ascii=False, indent=2)}

ALL STRENGTHS MENTIONED:
{json.dumps(all_strengths[:20], ensure_ascii=False, indent=2)}

ALL IMPROVEMENT AREAS / ISSUES:
{json.dumps(all_issues[:20], ensure_ascii=False, indent=2)}

REPRESENTATIVE QUOTES:
{json.dumps(all_quotes[:10], ensure_ascii=False, indent=2)}
"""
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are a senior HR strategy consultant preparing an executive report for a company's HR leadership team.

Based on the aggregated employee feedback data below, produce a comprehensive and professional executive report in **Markdown** format.

{data_summary}

The report MUST include the following sections:

# Executive Summary
A high-level overview of the overall employee sentiment, volume of feedback processed, and the most critical findings.

## Key Strengths
The top strengths and positive aspects mentioned across all feedback, with brief explanations.

## Key Problems & Concerns
The most frequently raised issues and areas of dissatisfaction, ranked by severity and frequency.

## Thematic Analysis
A breakdown of the most common themes/topics across feedback, with commentary on what they indicate about organizational health.

## Risk Areas
Identify any patterns that could indicate high-risk areas for the organization (e.g., high turnover risk, burnout, compliance gaps, management issues).

## Recommended Actions
A prioritized list of specific, actionable HR recommendations to address the findings. Each recommendation should be tied to a specific finding.

## Conclusion
A brief closing statement summarizing the overall takeaway and next steps.

RULES:
- Write in a professional, concise, executive-friendly tone.
- Use bullet points and sub-headings for readability.
- Do NOT invent data not present in the input.
- Output in Markdown format only.
"""

    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise RuntimeError(f"Mistral Report Generation failed (HTTP {response.status_code}): {response.text}")
    
    return response.json()["choices"][0]["message"]["content"]
