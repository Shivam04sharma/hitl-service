"""Query complexity analyzer for model switch recommendations."""

from typing import Dict


def analyze_query_complexity(text: str) -> Dict[str, any]:
    """Analyze query complexity to recommend model switch.
    
    Args:
        text: User query text
        
    Returns:
        Dict with complexity score and recommendation
    """
    score = 0.0
    reasons = []
    
    # Length-based complexity
    word_count = len(text.split())
    if word_count > 50:
        score += 0.3
        reasons.append("long_query")
    elif word_count > 30:
        score += 0.2
        reasons.append("medium_query")
    
    # Technical keywords
    technical_keywords = [
        "algorithm", "optimize", "architecture", "implement", "design",
        "analyze", "compare", "evaluate", "complex", "advanced",
        "integration", "system", "framework", "infrastructure", "quantum",
        "machine learning", "neural", "distributed", "microservices"
    ]
    tech_count = sum(1 for kw in technical_keywords if kw in text.lower())
    if tech_count >= 2:
        score += 0.3
        reasons.append("technical_content")
    
    # Code-related queries
    code_indicators = ["```", "function", "class", "def ", "import ", "const ", "var ", "code", "implementation"]
    if any(indicator in text.lower() for indicator in code_indicators):
        score += 0.3
        reasons.append("code_generation")
    
    # Multi-step reasoning indicators
    reasoning_keywords = ["step by step", "explain", "why", "how does", "what if", "detailed", "complete"]
    if any(kw in text.lower() for kw in reasoning_keywords):
        score += 0.2
        reasons.append("reasoning_required")
    
    # Normalize score to 0-1
    score = min(score, 1.0)
    
    return {
        "complexity_score": score,
        "is_complex": score >= 0.5,
        "reasons": reasons,
        "word_count": word_count,
    }


def suggest_model(complexity_score: float, current_model: str = "gemini-2.0-flash-lite") -> str:
    """Suggest appropriate model based on complexity.
    
    Args:
        complexity_score: Complexity score (0-1)
        current_model: Current model being used
        
    Returns:
        Suggested model name
    """
    # For Gemini models
    if "gemini" in current_model.lower():
        if complexity_score >= 0.7:
            return "gemini-1.5-pro"
        elif complexity_score >= 0.5:
            return "gemini-2.0-flash"
        else:
            return current_model
    
    # For GPT models
    if complexity_score >= 0.8:
        return "gpt-4o"
    elif complexity_score >= 0.6:
        return "gpt-4o-mini"
    else:
        return current_model
