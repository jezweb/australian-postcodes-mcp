"""Basic search tools for postcode and suburb lookup."""

from typing import Dict, Any, Optional, List
import logging

from database import get_database
from utils.config import Config

logger = logging.getLogger(__name__)

async def search_by_postcode(postcode: str) -> Dict[str, Any]:
    """
    Find all suburbs for a given postcode.
    
    Args:
        postcode: The postcode to search for
        
    Returns:
        Dictionary with suburbs and metadata
    """
    try:
        # Clean postcode
        postcode = postcode.strip()
        
        # Validate postcode format (4 digits)
        if not postcode.isdigit() or len(postcode) != 4:
            return {
                "status": "error",
                "error": f"Invalid postcode format: {postcode}. Must be 4 digits.",
                "suggestion": "Please enter a valid 4-digit Australian postcode"
            }
        
        db = await get_database()
        results = await db.search_by_postcode(postcode)
        
        if not results:
            return {
                "status": "error",
                "error": f"No suburbs found for postcode {postcode}",
                "suggestion": "Please check the postcode is correct"
            }
        
        # Group by state if multiple states have same postcode
        suburbs_by_state = {}
        for result in results:
            state = result['state']
            if state not in suburbs_by_state:
                suburbs_by_state[state] = []
            suburbs_by_state[state].append(result)
        
        return {
            "status": "success",
            "exact_match": True,
            "postcode": postcode,
            "suburbs": results,
            "suburbs_by_state": suburbs_by_state,
            "count": len(results),
            "validation_notes": [f"Found {len(results)} suburb(s) for postcode {postcode}"]
        }
        
    except Exception as e:
        logger.error(f"Error searching by postcode: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def search_by_suburb(
    suburb: str,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find postcodes for a suburb name.
    
    Args:
        suburb: Suburb name to search for
        state: Optional state filter (e.g., "NSW", "VIC")
        
    Returns:
        Dictionary with postcodes and metadata
    """
    try:
        # Clean inputs
        suburb = suburb.strip()
        if state:
            state = state.strip().upper()
            
            # Validate state
            if state not in Config.STATES:
                return {
                    "status": "error",
                    "error": f"Invalid state: {state}",
                    "suggestion": f"Valid states are: {', '.join(Config.STATES.keys())}"
                }
        
        db = await get_database()
        results = await db.search_by_suburb(suburb, state)
        
        if not results:
            # No exact match, will be handled by fuzzy search in real usage
            return {
                "status": "error",
                "exact_match": False,
                "error": f"No exact match found for suburb '{suburb}'",
                "suggestion": "Try using the fuzzy search tool for suggestions"
            }
        
        # Check if multiple states have this suburb
        states_found = list(set(r['state'] for r in results))
        
        response = {
            "status": "success",
            "exact_match": True,
            "suburb": suburb,
            "results": results,
            "count": len(results)
        }
        
        if len(states_found) > 1 and not state:
            response["multiple_states"] = True
            response["states_found"] = states_found
            response["suggestion"] = f"Suburb '{suburb}' exists in multiple states. Consider specifying the state."
        
        # Extract unique postcodes
        postcodes = list(set(r['postcode'] for r in results))
        response["postcodes"] = sorted(postcodes)
        
        if len(postcodes) == 1:
            response["postcode"] = postcodes[0]
        
        return response
        
    except Exception as e:
        logger.error(f"Error searching by suburb: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def validate_suburb_postcode(
    suburb: str,
    postcode: str,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate if a suburb-postcode combination is correct.
    
    Args:
        suburb: Suburb name
        postcode: Postcode
        state: Optional state for disambiguation
        
    Returns:
        Validation result with confidence
    """
    try:
        # Clean inputs
        suburb = suburb.strip()
        postcode = postcode.strip()
        
        # Validate postcode format
        if not postcode.isdigit() or len(postcode) != 4:
            return {
                "status": "error",
                "valid": False,
                "error": f"Invalid postcode format: {postcode}",
                "confidence": 0.0
            }
        
        db = await get_database()
        is_valid = await db.validate_combination(suburb, postcode, state)
        
        if is_valid:
            # Get full details for valid combination
            results = await db.search_by_suburb(suburb, state)
            matching = [r for r in results if r['postcode'] == postcode]
            
            return {
                "status": "success",
                "valid": True,
                "confidence": 1.0,
                "details": matching[0] if matching else None,
                "validation_notes": [f"'{suburb}' with postcode {postcode} is valid"]
            }
        else:
            # Check what's wrong
            postcode_results = await db.search_by_postcode(postcode)
            suburb_results = await db.search_by_suburb(suburb, state)
            
            suggestions = []
            if postcode_results:
                suburbs_for_postcode = [r['locality'] for r in postcode_results]
                suggestions.append(f"Postcode {postcode} is valid for: {', '.join(suburbs_for_postcode[:3])}")
            
            if suburb_results:
                postcodes_for_suburb = [r['postcode'] for r in suburb_results]
                suggestions.append(f"Suburb '{suburb}' has postcode(s): {', '.join(postcodes_for_suburb[:3])}")
            
            return {
                "status": "error",
                "valid": False,
                "confidence": 0.0,
                "error": f"Invalid combination: '{suburb}' with postcode {postcode}",
                "suggestions": suggestions if suggestions else ["Please check both suburb and postcode"]
            }
        
    except Exception as e:
        logger.error(f"Error validating suburb-postcode: {e}")
        return {
            "status": "error",
            "valid": False,
            "confidence": 0.0,
            "error": str(e)
        }

async def get_location_details(query: str) -> Dict[str, Any]:
    """
    Smart search that accepts either postcode or suburb name.
    
    Args:
        query: Can be a postcode (4 digits) or suburb name
        
    Returns:
        Location details with all available information
    """
    try:
        query = query.strip()
        
        # Detect query type
        is_postcode = query.isdigit() and len(query) == 4
        
        if is_postcode:
            # Search by postcode
            result = await search_by_postcode(query)
            if result.get("status") == "success":
                # Enhance with additional details
                result["query_type"] = "postcode"
                result["input"] = query
        else:
            # Search by suburb - try to extract state if provided
            parts = query.split(",")
            suburb = parts[0].strip()
            state = parts[1].strip().upper() if len(parts) > 1 else None
            
            # Validate state if provided
            if state and state not in Config.STATES:
                # Maybe it's a state name, try to find abbreviation
                state_name_lower = state.lower()
                state = None
                for abbr, name in Config.STATES.items():
                    if name.lower() == state_name_lower:
                        state = abbr
                        break
            
            result = await search_by_suburb(suburb, state)
            if result.get("status") == "success":
                result["query_type"] = "suburb"
                result["input"] = query
            else:
                # If no exact match, return error suggesting fuzzy search
                result["suggestion"] = "No exact match found. Try using the fuzzy search tool for suggestions."
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting location details: {e}")
        return {
            "status": "error",
            "error": str(e),
            "input": query
        }