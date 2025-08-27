"""Location-based tools for LGA, radius, and neighboring suburb queries."""

from typing import Dict, Any, Optional, List
import logging

from database import get_database
from utils.config import Config

logger = logging.getLogger(__name__)

async def list_suburbs_in_lga(
    lga_name: str,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all suburbs in a Local Government Area (city/council area).
    
    Args:
        lga_name: Name of the LGA (e.g., "Newcastle", "Sydney")
        state: Optional state filter
        
    Returns:
        Dictionary with all suburbs and postcodes in the LGA
    """
    try:
        lga_name = lga_name.strip()
        
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
        results = await db.search_by_lga(lga_name, state)
        
        if not results:
            return {
                "status": "error",
                "error": f"No LGA found matching '{lga_name}'",
                "suggestion": "Please check the LGA name or try a partial match"
            }
        
        # Group results by suburb
        suburbs_dict = {}
        for result in results:
            suburb = result['locality']
            if suburb not in suburbs_dict:
                suburbs_dict[suburb] = {
                    "suburb": suburb,
                    "postcodes": set(),
                    "state": result['state'],
                    "lga_name": result['lga_name']
                }
            suburbs_dict[suburb]["postcodes"].add(result['postcode'])
        
        # Convert sets to sorted lists
        suburbs_list = []
        for suburb_data in suburbs_dict.values():
            suburbs_list.append({
                "suburb": suburb_data["suburb"],
                "postcodes": sorted(list(suburb_data["postcodes"])),
                "state": suburb_data["state"],
                "lga_name": suburb_data["lga_name"]
            })
        
        # Sort by suburb name
        suburbs_list.sort(key=lambda x: x["suburb"])
        
        # Extract unique LGA names found
        unique_lgas = list(set(r['lga_name'] for r in results if r['lga_name']))
        
        return {
            "status": "success",
            "query": lga_name,
            "lga_names_found": unique_lgas,
            "suburbs": suburbs_list,
            "suburb_count": len(suburbs_list),
            "total_postcodes": len(set(r['postcode'] for r in results)),
            "validation_notes": [
                f"Found {len(suburbs_list)} suburb(s) in LGA matching '{lga_name}'"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing suburbs in LGA: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def find_lga_for_suburb(
    suburb: str,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find the Local Government Area (city/council) for a suburb.
    
    Args:
        suburb: Suburb name
        state: Optional state filter
        
    Returns:
        LGA information for the suburb
    """
    try:
        suburb = suburb.strip()
        
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
        results = await db.search_by_suburb(suburb, state)
        
        if not results:
            return {
                "status": "error",
                "error": f"Suburb '{suburb}' not found",
                "suggestion": "Please check the spelling or use the fuzzy search tool"
            }
        
        # Extract unique LGAs
        lgas = {}
        for result in results:
            if result.get('lga_name'):
                lga_key = (result['lga_name'], result.get('lga_code'), result['state'])
                if lga_key not in lgas:
                    lgas[lga_key] = {
                        "lga_name": result['lga_name'],
                        "lga_code": result.get('lga_code'),
                        "state": result['state'],
                        "postcodes": set()
                    }
                lgas[lga_key]["postcodes"].add(result['postcode'])
        
        # Convert to list and sort postcodes
        lga_list = []
        for lga_data in lgas.values():
            lga_data["postcodes"] = sorted(list(lga_data["postcodes"]))
            lga_list.append(lga_data)
        
        if not lga_list:
            return {
                "status": "success",
                "suburb": suburb,
                "lga": None,
                "message": f"No LGA information available for '{suburb}'",
                "validation_notes": ["Some suburbs may not have LGA data"]
            }
        
        # Primary result is first LGA (or filtered by state)
        primary_lga = lga_list[0] if lga_list else None
        
        response = {
            "status": "success",
            "suburb": suburb,
            "primary_lga": primary_lga,
            "all_lgas": lga_list
        }
        
        if len(lga_list) > 1:
            response["multiple_lgas"] = True
            response["suggestion"] = f"Suburb '{suburb}' spans multiple LGAs"
        
        response["validation_notes"] = [
            f"Found LGA information for '{suburb}'"
        ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error finding LGA for suburb: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def list_suburbs_in_radius(
    postcode_or_suburb: str,
    radius_km: float,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find all suburbs within a radius of a location.
    
    Args:
        postcode_or_suburb: Center point (postcode or suburb name)
        radius_km: Search radius in kilometers
        state: Optional state filter
        
    Returns:
        Suburbs within the specified radius
    """
    try:
        center = postcode_or_suburb.strip()
        
        # Validate radius
        if radius_km <= 0 or radius_km > 500:
            return {
                "status": "error",
                "error": f"Invalid radius: {radius_km}km",
                "suggestion": "Radius must be between 1 and 500 kilometers"
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
        
        # Find center coordinates
        center_coords = None
        center_info = {}
        
        # Check if it's a postcode
        if center.isdigit() and len(center) == 4:
            results = await db.search_by_postcode(center)
            if results:
                # Use first result with coordinates
                for r in results:
                    if r.get('latitude') and r.get('longitude'):
                        center_coords = (r['latitude'], r['longitude'])
                        center_info = {
                            "type": "postcode",
                            "postcode": center,
                            "suburb": r['locality'],
                            "state": r['state']
                        }
                        break
        else:
            # It's a suburb name
            results = await db.search_by_suburb(center, state)
            if results:
                # Use first result with coordinates
                for r in results:
                    if r.get('latitude') and r.get('longitude'):
                        center_coords = (r['latitude'], r['longitude'])
                        center_info = {
                            "type": "suburb",
                            "suburb": r['locality'],
                            "postcode": r['postcode'],
                            "state": r['state']
                        }
                        break
        
        if not center_coords:
            return {
                "status": "error",
                "error": f"Location '{center}' not found or has no coordinates",
                "suggestion": "Please check the location name or postcode"
            }
        
        # Search within radius
        results = await db.search_by_radius(
            center_coords[0],
            center_coords[1],
            radius_km
        )
        
        # Group by suburb to avoid duplicates
        suburbs_dict = {}
        for result in results:
            suburb_key = (result['locality'], result['state'])
            if suburb_key not in suburbs_dict:
                suburbs_dict[suburb_key] = {
                    "suburb": result['locality'],
                    "state": result['state'],
                    "postcodes": set(),
                    "distance_km": result.get('distance_km', 0),
                    "lga_name": result.get('lga_name')
                }
            suburbs_dict[suburb_key]["postcodes"].add(result['postcode'])
            # Keep minimum distance
            if result.get('distance_km', 0) < suburbs_dict[suburb_key]["distance_km"]:
                suburbs_dict[suburb_key]["distance_km"] = result.get('distance_km', 0)
        
        # Convert to list
        nearby_suburbs = []
        for suburb_data in suburbs_dict.values():
            nearby_suburbs.append({
                "suburb": suburb_data["suburb"],
                "state": suburb_data["state"],
                "postcodes": sorted(list(suburb_data["postcodes"])),
                "distance_km": round(suburb_data["distance_km"], 1),
                "lga_name": suburb_data["lga_name"]
            })
        
        # Sort by distance
        nearby_suburbs.sort(key=lambda x: x["distance_km"])
        
        return {
            "status": "success",
            "center": center_info,
            "center_coordinates": {
                "latitude": center_coords[0],
                "longitude": center_coords[1]
            },
            "radius_km": radius_km,
            "suburbs": nearby_suburbs,
            "suburb_count": len(nearby_suburbs),
            "validation_notes": [
                f"Found {len(nearby_suburbs)} suburb(s) within {radius_km}km of {center}"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching suburbs in radius: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def get_neighboring_suburbs(
    suburb: str,
    state: Optional[str] = None,
    max_neighbors: int = 10
) -> Dict[str, Any]:
    """
    Find neighboring suburbs (adjacent areas).
    
    Args:
        suburb: Suburb name
        state: Optional state filter
        max_neighbors: Maximum number of neighbors to return
        
    Returns:
        List of neighboring suburbs
    """
    try:
        suburb = suburb.strip()
        
        # Validate state if provided
        if state:
            state = state.strip().upper()
            if state not in Config.STATES:
                return {
                    "status": "error",
                    "error": f"Invalid state: {state}"
                }
        
        # Validate max_neighbors
        if max_neighbors < 1 or max_neighbors > 50:
            max_neighbors = 10
        
        db = await get_database()
        
        # Find the suburb's coordinates
        results = await db.search_by_suburb(suburb, state)
        
        if not results:
            return {
                "status": "error",
                "error": f"Suburb '{suburb}' not found",
                "suggestion": "Please check the spelling or use the fuzzy search tool"
            }
        
        # Get coordinates from first result with location data
        center_coords = None
        center_info = None
        for result in results:
            if result.get('latitude') and result.get('longitude'):
                center_coords = (result['latitude'], result['longitude'])
                center_info = {
                    "suburb": result['locality'],
                    "postcode": result['postcode'],
                    "state": result['state'],
                    "lga_name": result.get('lga_name')
                }
                break
        
        if not center_coords:
            return {
                "status": "error",
                "error": f"No coordinates available for '{suburb}'",
                "suggestion": "Cannot find neighbors without location data"
            }
        
        # Search within small radius (typically 5-10km for neighbors)
        # Adjust based on typical suburb size in Australia
        search_radius = 8.0  # km
        
        nearby_results = await db.search_by_radius(
            center_coords[0],
            center_coords[1],
            search_radius
        )
        
        # Filter out the original suburb and group by suburb
        neighbors_dict = {}
        for result in nearby_results:
            # Skip the original suburb
            if result['locality'].lower() == suburb.lower():
                continue
            
            suburb_key = (result['locality'], result['state'])
            if suburb_key not in neighbors_dict:
                neighbors_dict[suburb_key] = {
                    "suburb": result['locality'],
                    "state": result['state'],
                    "postcodes": set(),
                    "distance_km": result.get('distance_km', 0),
                    "lga_name": result.get('lga_name'),
                    "direction": None  # Could calculate compass direction
                }
            neighbors_dict[suburb_key]["postcodes"].add(result['postcode'])
            # Keep minimum distance
            if result.get('distance_km', 0) < neighbors_dict[suburb_key]["distance_km"]:
                neighbors_dict[suburb_key]["distance_km"] = result.get('distance_km', 0)
        
        # Convert to list and sort by distance
        neighbors = []
        for neighbor_data in neighbors_dict.values():
            neighbors.append({
                "suburb": neighbor_data["suburb"],
                "state": neighbor_data["state"],
                "postcodes": sorted(list(neighbor_data["postcodes"])),
                "distance_km": round(neighbor_data["distance_km"], 1),
                "lga_name": neighbor_data["lga_name"]
            })
        
        # Sort by distance and limit
        neighbors.sort(key=lambda x: x["distance_km"])
        neighbors = neighbors[:max_neighbors]
        
        # Check if same LGA (true neighbors often share LGA)
        if center_info.get('lga_name'):
            for neighbor in neighbors:
                if neighbor.get('lga_name') == center_info['lga_name']:
                    neighbor['same_lga'] = True
        
        return {
            "status": "success",
            "query_suburb": center_info,
            "neighbors": neighbors,
            "neighbor_count": len(neighbors),
            "search_radius_km": search_radius,
            "validation_notes": [
                f"Found {len(neighbors)} neighboring suburb(s) for '{suburb}'"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error finding neighboring suburbs: {e}")
        return {
            "status": "error",
            "error": str(e)
        }