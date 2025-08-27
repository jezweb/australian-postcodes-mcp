"""Validation and fuzzy matching tools for suburb names."""

from typing import Dict, Any, Optional, List
import logging

from database import get_database
from utils.config import Config
from utils.fuzzy_match import (
    smart_match,
    phonetic_match,
    find_best_matches,
    handle_compound_words
)

logger = logging.getLogger(__name__)

async def find_similar_suburbs(
    misspelled: str,
    state: Optional[str] = None,
    threshold: float = None
) -> Dict[str, Any]:
    """
    Find similar suburbs for a possibly misspelled name.
    
    Args:
        misspelled: Potentially misspelled suburb name
        state: Optional state filter
        threshold: Similarity threshold (0-1)
        
    Returns:
        Dictionary with matched suburbs and confidence scores
    """
    try:
        misspelled = misspelled.strip()
        threshold = threshold or Config.FUZZY_THRESHOLD
        
        # Validate state if provided
        if state:
            state = state.strip().upper()
            if state not in Config.STATES:
                return {
                    "status": "error",
                    "error": f"Invalid state: {state}",
                    "suggestion": f"Valid states are: {', '.join(Config.STATES.keys())}"
                }
        
        db = await get_database()
        
        # First check for exact match (case-insensitive)
        exact_results = await db.search_by_suburb(misspelled, state)
        if exact_results:
            return {
                "status": "success",
                "exact_match": True,
                "confidence": 1.0,
                "primary_result": exact_results[0],
                "all_results": exact_results,
                "validation_notes": ["Exact match found"]
            }
        
        # Get all suburbs for fuzzy matching
        all_suburbs = await db.get_all_suburbs(state)
        
        # Perform smart matching (fuzzy + phonetic)
        matches = smart_match(
            misspelled,
            all_suburbs,
            use_fuzzy=True,
            use_phonetic=True
        )
        
        if not matches:
            # Try with looser threshold
            matches = find_best_matches(
                misspelled,
                all_suburbs,
                threshold=threshold * 0.7,
                limit=Config.MAX_SUGGESTIONS
            )
        
        if not matches:
            return {
                "status": "error",
                "exact_match": False,
                "confidence": 0.0,
                "error": f"No similar suburbs found for '{misspelled}'",
                "suggestion": "Please check the spelling or try a different search"
            }
        
        # Get full details for matched suburbs
        suggestions = []
        for match in matches:
            suburb_details = await db.search_by_suburb(match['match'], state)
            if suburb_details:
                suggestions.append({
                    "suburb": match['match'],
                    "confidence": match['confidence'],
                    "match_type": match.get('match_type', 'fuzzy'),
                    "postcodes": [r['postcode'] for r in suburb_details],
                    "states": list(set(r['state'] for r in suburb_details))
                })
        
        # Determine best match
        best_match = suggestions[0] if suggestions else None
        
        return {
            "status": "success",
            "exact_match": False,
            "confidence": best_match['confidence'] if best_match else 0.0,
            "primary_result": best_match,
            "suggestions": suggestions,
            "query": misspelled,
            "suggestion": f"Did you mean '{best_match['suburb']}'?" if best_match else None,
            "validation_notes": [
                f"Found {len(suggestions)} similar suburb(s)",
                f"Best match: {best_match['suburb']} ({best_match['confidence']:.2f} confidence)" if best_match else ""
            ]
        }
        
    except Exception as e:
        logger.error(f"Error finding similar suburbs: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def autocomplete_suburb(
    partial: str,
    state: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Provide autocomplete suggestions for partial suburb names.
    
    Args:
        partial: Partial suburb name (minimum 2 characters)
        state: Optional state filter
        limit: Maximum number of suggestions
        
    Returns:
        Dictionary with autocomplete suggestions
    """
    try:
        partial = partial.strip()
        
        # Require minimum length
        if len(partial) < 2:
            return {
                "status": "error",
                "error": "Please enter at least 2 characters",
                "suggestions": []
            }
        
        # Validate state if provided
        if state:
            state = state.strip().upper()
            if state not in Config.STATES:
                return {
                    "status": "error",
                    "error": f"Invalid state: {state}"
                }
        
        db = await get_database()
        
        # Use fuzzy search with prefix matching
        results = await db.search_fuzzy(partial, state, limit=limit * 2)
        
        # Also get exact prefix matches
        all_suburbs = await db.get_all_suburbs(state)
        prefix_matches = [
            s for s in all_suburbs
            if s.lower().startswith(partial.lower())
        ]
        
        # Combine and deduplicate
        suggestions = []
        seen = set()
        
        # Add prefix matches first (higher priority)
        for suburb in prefix_matches[:limit]:
            if suburb not in seen:
                details = await db.search_by_suburb(suburb, state)
                if details:
                    suggestions.append({
                        "suburb": suburb,
                        "match_type": "prefix",
                        "states": list(set(r['state'] for r in details)),
                        "postcodes": list(set(r['postcode'] for r in details))
                    })
                    seen.add(suburb)
        
        # Add fuzzy matches
        for result in results:
            if result['locality'] not in seen and len(suggestions) < limit:
                suggestions.append({
                    "suburb": result['locality'],
                    "match_type": "fuzzy",
                    "state": result['state'],
                    "postcode": result['postcode']
                })
                seen.add(result['locality'])
        
        return {
            "status": "success",
            "query": partial,
            "suggestions": suggestions[:limit],
            "count": len(suggestions),
            "validation_notes": [f"Found {len(suggestions)} suggestion(s) for '{partial}'"]
        }
        
    except Exception as e:
        logger.error(f"Error in autocomplete: {e}")
        return {
            "status": "error",
            "error": str(e),
            "suggestions": []
        }

async def validate_spelling(suburb: str) -> Dict[str, Any]:
    """
    Check spelling and suggest corrections for suburb names.
    
    Args:
        suburb: Suburb name to validate
        
    Returns:
        Validation result with spelling suggestions
    """
    try:
        suburb = suburb.strip()
        
        db = await get_database()
        
        # Check if it's already correct
        exact_results = await db.search_by_suburb(suburb)
        if exact_results:
            return {
                "status": "success",
                "spelling_correct": True,
                "suburb": suburb,
                "confidence": 1.0,
                "validation_notes": ["Spelling is correct"],
                "details": exact_results
            }
        
        # Find similar suburbs
        all_suburbs = await db.get_all_suburbs()
        
        # Use fuzzy matching to find corrections
        matches = find_best_matches(
            suburb,
            all_suburbs,
            threshold=0.7,  # Lower threshold for spelling corrections
            limit=5
        )
        
        if not matches:
            return {
                "status": "error",
                "spelling_correct": False,
                "error": f"No similar suburbs found for '{suburb}'",
                "confidence": 0.0
            }
        
        # Format corrections
        corrections = []
        for match in matches:
            details = await db.search_by_suburb(match['match'])
            if details:
                corrections.append({
                    "suburb": match['match'],
                    "confidence": match['confidence'],
                    "states": list(set(r['state'] for r in details)),
                    "postcodes": list(set(r['postcode'] for r in details))
                })
        
        best_match = corrections[0] if corrections else None
        
        return {
            "status": "success",
            "spelling_correct": False,
            "query": suburb,
            "confidence": best_match['confidence'] if best_match else 0.0,
            "suggested_spelling": best_match['suburb'] if best_match else None,
            "corrections": corrections,
            "suggestion": f"Did you mean '{best_match['suburb']}'?" if best_match else None,
            "validation_notes": [
                f"Spelling appears incorrect",
                f"Found {len(corrections)} possible correction(s)"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error validating spelling: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def phonetic_search(spoken_name: str) -> Dict[str, Any]:
    """
    Search for suburbs based on phonetic similarity (for voice input).
    
    Args:
        spoken_name: Suburb name as heard/spoken
        
    Returns:
        Phonetically similar suburbs
    """
    try:
        spoken_name = spoken_name.strip()
        
        db = await get_database()
        
        # First check exact match
        exact_results = await db.search_by_suburb(spoken_name)
        if exact_results:
            return {
                "status": "success",
                "exact_match": True,
                "confidence": 1.0,
                "results": exact_results,
                "match_type": "exact",
                "validation_notes": ["Exact match found"]
            }
        
        # Handle compound word variations
        variations = handle_compound_words(spoken_name)
        
        all_matches = []
        for variant in variations:
            # Try exact match for variant
            variant_results = await db.search_by_suburb(variant)
            if variant_results:
                return {
                    "status": "success",
                    "exact_match": True,
                    "confidence": 0.95,  # Slightly lower for variant match
                    "results": variant_results,
                    "match_type": "compound_variant",
                    "original_query": spoken_name,
                    "matched_variant": variant,
                    "validation_notes": [f"Found match for variant: '{variant}'"]
                }
        
        # Get all suburbs for phonetic matching
        all_suburbs = await db.get_all_suburbs()
        
        # Perform phonetic matching
        phonetic_matches = phonetic_match(
            spoken_name,
            all_suburbs,
            threshold=Config.PHONETIC_THRESHOLD
        )
        
        if not phonetic_matches:
            # Try with variations
            for variant in variations[1:]:  # Skip first (original)
                phonetic_matches = phonetic_match(
                    variant,
                    all_suburbs,
                    threshold=Config.PHONETIC_THRESHOLD * 0.9
                )
                if phonetic_matches:
                    break
        
        if not phonetic_matches:
            return {
                "status": "error",
                "exact_match": False,
                "confidence": 0.0,
                "error": f"No phonetic matches found for '{spoken_name}'",
                "suggestion": "Please try spelling the suburb name differently"
            }
        
        # Get full details for matches
        results = []
        for match in phonetic_matches:
            suburb_details = await db.search_by_suburb(match['match'])
            if suburb_details:
                results.append({
                    "suburb": match['match'],
                    "confidence": match['confidence'],
                    "match_type": "phonetic",
                    "postcodes": [r['postcode'] for r in suburb_details],
                    "states": list(set(r['state'] for r in suburb_details))
                })
        
        best_match = results[0] if results else None
        
        return {
            "status": "success",
            "exact_match": False,
            "confidence": best_match['confidence'] if best_match else 0.0,
            "spoken_input": spoken_name,
            "primary_result": best_match,
            "phonetic_matches": results,
            "suggestion": f"Did you say '{best_match['suburb']}'?" if best_match else None,
            "validation_notes": [
                f"Found {len(results)} phonetic match(es)",
                "These suburbs sound similar to what was spoken"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in phonetic search: {e}")
        return {
            "status": "error",
            "error": str(e)
        }