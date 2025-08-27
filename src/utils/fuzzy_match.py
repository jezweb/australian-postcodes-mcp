"""Fuzzy matching utilities for suburb names."""

from typing import List, Tuple, Optional, Dict
from rapidfuzz import fuzz, process
from metaphone import doublemetaphone
from .config import Config

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize strings
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    # Use token sort ratio for better matching of word order variations
    score = fuzz.token_sort_ratio(str1, str2) / 100.0
    return score

def phonetic_encode(text: str) -> Tuple[str, str]:
    """
    Generate phonetic encoding for a text.
    
    Args:
        text: Text to encode
        
    Returns:
        Tuple of primary and secondary phonetic codes
    """
    # Clean text
    text = text.lower().strip()
    
    # Expand common abbreviations first
    text = expand_abbreviations(text)
    
    # Generate double metaphone codes
    primary, secondary = doublemetaphone(text)
    return primary or "", secondary or ""

def expand_abbreviations(text: str) -> str:
    """
    Expand common Australian address abbreviations.
    
    Args:
        text: Text with potential abbreviations
        
    Returns:
        Text with expanded abbreviations
    """
    words = text.split()
    expanded = []
    
    for word in words:
        # Check if word is an abbreviation
        for abbr, full in Config.ABBREVIATIONS.items():
            if word.lower() == abbr.lower():
                word = full
                break
        expanded.append(word)
    
    return " ".join(expanded)

def find_best_matches(
    query: str,
    candidates: List[str],
    threshold: float = 0.8,
    limit: int = 5
) -> List[Dict[str, any]]:
    """
    Find best fuzzy matches from a list of candidates.
    
    Args:
        query: Search query
        candidates: List of candidate strings
        threshold: Minimum similarity threshold (0-1)
        limit: Maximum number of results
        
    Returns:
        List of matches with scores
    """
    # Expand abbreviations in query
    expanded_query = expand_abbreviations(query)
    
    # Get fuzzy matches
    matches = process.extract(
        expanded_query,
        candidates,
        scorer=fuzz.token_sort_ratio,
        limit=limit * 2  # Get extra to filter by threshold
    )
    
    # Filter by threshold and format results
    results = []
    for match, score, _ in matches:
        confidence = score / 100.0
        if confidence >= threshold:
            results.append({
                "match": match,
                "confidence": round(confidence, 3),
                "score": score
            })
    
    return results[:limit]

def phonetic_match(
    query: str,
    candidates: List[str],
    threshold: float = 0.85
) -> List[Dict[str, any]]:
    """
    Find matches based on phonetic similarity.
    
    Args:
        query: Search query
        candidates: List of candidate strings
        threshold: Minimum similarity threshold
        
    Returns:
        List of phonetic matches
    """
    query_primary, query_secondary = phonetic_encode(query)
    matches = []
    
    for candidate in candidates:
        cand_primary, cand_secondary = phonetic_encode(candidate)
        
        # Check if phonetic codes match
        if query_primary and (
            query_primary == cand_primary or
            query_primary == cand_secondary or
            (query_secondary and query_secondary == cand_primary)
        ):
            # Calculate string similarity as secondary check
            similarity = calculate_similarity(query, candidate)
            if similarity >= threshold * 0.7:  # Lower threshold for phonetic matches
                matches.append({
                    "match": candidate,
                    "confidence": min(0.95, similarity + 0.1),  # Boost confidence for phonetic match
                    "match_type": "phonetic"
                })
    
    # Sort by confidence
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches[:Config.MAX_SUGGESTIONS]

def handle_compound_words(text: str) -> List[str]:
    """
    Handle compound word variations (e.g., "New Castle" vs "Newcastle").
    
    Args:
        text: Input text
        
    Returns:
        List of possible variations
    """
    variations = [text]
    
    # Try joining words
    words = text.split()
    if len(words) > 1:
        # Join all words
        variations.append("".join(words))
        
        # Try common patterns
        if len(words) == 2:
            # Join first two words only
            variations.append(words[0] + words[1])
    
    # Try splitting compound words (basic approach)
    if len(text) > 6 and " " not in text:
        # Common compound patterns in Australian suburbs
        patterns = [
            ("New", 4),  # Newcastle, Newtown
            ("North", 5),  # Northbridge
            ("South", 5),  # Southport
            ("East", 4),  # Eastwood
            ("West", 4),  # Westmead
            ("Upper", 5),  # Uppercross
            ("Lower", 5),  # Lowercase
            ("Port", 4),  # Portarlington
            ("Mount", 5),  # Mountview
        ]
        
        for prefix, length in patterns:
            if text.lower().startswith(prefix.lower()):
                variations.append(f"{text[:length]} {text[length:]}")
    
    return variations

def smart_match(
    query: str,
    candidates: List[str],
    use_fuzzy: bool = True,
    use_phonetic: bool = True
) -> List[Dict[str, any]]:
    """
    Perform smart matching using multiple strategies.
    
    Args:
        query: Search query
        candidates: List of candidate strings
        use_fuzzy: Enable fuzzy matching
        use_phonetic: Enable phonetic matching
        
    Returns:
        Combined and ranked matches
    """
    all_matches = {}
    
    # Try exact match first
    query_lower = query.lower().strip()
    for candidate in candidates:
        if candidate.lower().strip() == query_lower:
            return [{
                "match": candidate,
                "confidence": 1.0,
                "match_type": "exact"
            }]
    
    # Handle compound word variations
    variations = handle_compound_words(query)
    
    for variant in variations:
        # Fuzzy matching
        if use_fuzzy and Config.ENABLE_FUZZY_MATCHING:
            fuzzy_matches = find_best_matches(
                variant,
                candidates,
                threshold=Config.FUZZY_THRESHOLD
            )
            for match in fuzzy_matches:
                key = match["match"]
                if key not in all_matches or match["confidence"] > all_matches[key]["confidence"]:
                    match["match_type"] = "fuzzy"
                    all_matches[key] = match
        
        # Phonetic matching
        if use_phonetic and Config.ENABLE_PHONETIC_SEARCH:
            phonetic_matches = phonetic_match(
                variant,
                candidates,
                threshold=Config.PHONETIC_THRESHOLD
            )
            for match in phonetic_matches:
                key = match["match"]
                if key not in all_matches or match["confidence"] > all_matches[key]["confidence"]:
                    all_matches[key] = match
    
    # Sort by confidence and return top matches
    results = list(all_matches.values())
    results.sort(key=lambda x: x["confidence"], reverse=True)
    
    return results[:Config.MAX_SUGGESTIONS]