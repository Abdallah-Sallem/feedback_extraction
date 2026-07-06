from collections import Counter

def compute_aggregation(documents):
    """
    Aggregates statistics from a list of analyzed documents.
    
    Args:
        documents (list): List of dictionaries, each representing an analyzed document.
        
    Returns:
        dict: Aggregated analytics.
    """
    total = len(documents)
    if total == 0:
        return {
            "total_count": 0,
            "sentiment_distribution": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "average_score": 0.0,
            "theme_counts": [],
            "all_strengths": [],
            "all_improvement_areas": [],
            "recent_quotes": []
        }
        
    # Sentiment distribution
    sentiments = [d.get("overall_sentiment", "Neutral") for d in documents]
    sentiment_counts = Counter(sentiments)
    # Ensure all categories exist
    sentiment_dist = {
        "Positive": sentiment_counts.get("Positive", 0),
        "Neutral": sentiment_counts.get("Neutral", 0),
        "Negative": sentiment_counts.get("Negative", 0)
    }
    
    # Average score
    scores = [d.get("sentiment_score", 5.0) for d in documents if d.get("sentiment_score") is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 5.0
    
    # Theme counts
    all_themes = []
    for d in documents:
        all_themes.extend(d.get("themes", []))
    
    # Normalize themes to title case for consistent aggregation
    normalized_themes = [theme.strip().title() for theme in all_themes if theme.strip()]
    theme_counts = Counter(normalized_themes).most_common()
    
    # Collect all strengths, improvement areas and quotes
    all_strengths = []
    all_improvement_areas = []
    all_quotes = []
    
    for d in documents:
        all_strengths.extend(d.get("strengths", []))
        all_improvement_areas.extend(d.get("improvement_areas", []))
        all_quotes.extend(d.get("quotes", []))
        
    return {
        "total_count": total,
        "sentiment_distribution": sentiment_dist,
        "average_score": avg_score,
        "theme_counts": theme_counts,
        "all_strengths": list(set(all_strengths)), # Remove duplicates if any
        "all_improvement_areas": list(set(all_improvement_areas)),
        "all_quotes": list(set(all_quotes))
    }
