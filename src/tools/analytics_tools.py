"""Analytics and statistics tools for database insights."""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from database import get_database
from utils.config import Config

logger = logging.getLogger(__name__)

async def get_state_statistics(state: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a state or all states.
    
    Args:
        state: Optional state code (e.g., "NSW", "VIC")
        
    Returns:
        Statistics about postcodes, suburbs, and LGAs
    """
    try:
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
        stats = await db.get_statistics()
        
        if state:
            # Filter for specific state
            if state not in stats.get('by_state', {}):
                return {
                    "status": "error",
                    "error": f"No data found for state: {state}"
                }
            
            state_data = stats['by_state'][state]
            
            # Get unique LGAs for the state
            lgas = await db.get_all_lgas(state)
            
            return {
                "status": "success",
                "state": state,
                "state_name": Config.STATES.get(state, state),
                "statistics": {
                    "total_postcodes": state_data.get('postcodes', 0),
                    "total_suburbs": state_data.get('suburbs', 0),
                    "total_lgas": len(lgas),
                    "lga_list": [lga['lga_name'] for lga in lgas if lga['lga_name']]
                },
                "validation_notes": [
                    f"Statistics for {Config.STATES.get(state, state)}"
                ]
            }
        else:
            # Return statistics for all states
            all_states_stats = []
            for state_code, state_data in stats.get('by_state', {}).items():
                all_states_stats.append({
                    "state": state_code,
                    "state_name": Config.STATES.get(state_code, state_code),
                    "postcodes": state_data.get('postcodes', 0),
                    "suburbs": state_data.get('suburbs', 0)
                })
            
            # Sort by state code
            all_states_stats.sort(key=lambda x: x['state'])
            
            return {
                "status": "success",
                "national_statistics": {
                    "total_records": stats.get('total_records', 0),
                    "unique_postcodes": stats.get('unique_postcodes', 0),
                    "unique_suburbs": stats.get('unique_suburbs', 0),
                    "unique_lgas": stats.get('unique_lgas', 0)
                },
                "by_state": all_states_stats,
                "validation_notes": [
                    "National statistics for all Australian states and territories"
                ]
            }
        
    except Exception as e:
        logger.error(f"Error getting state statistics: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def list_all_lgas(
    state: Optional[str] = None,
    include_suburbs_count: bool = False
) -> Dict[str, Any]:
    """
    List all Local Government Areas with optional suburb counts.
    
    Args:
        state: Optional state filter
        include_suburbs_count: Include count of suburbs in each LGA
        
    Returns:
        List of all LGAs with metadata
    """
    try:
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
        lgas = await db.get_all_lgas(state)
        
        if not lgas:
            return {
                "status": "error",
                "error": "No LGAs found",
                "suggestion": "Database may not contain LGA information"
            }
        
        # Enhance with suburb counts if requested
        lga_list = []
        for lga in lgas:
            if not lga.get('lga_name'):
                continue
            
            lga_info = {
                "lga_name": lga['lga_name'],
                "lga_code": lga.get('lga_code'),
                "state": lga['state'],
                "state_name": Config.STATES.get(lga['state'], lga['state'])
            }
            
            if include_suburbs_count:
                # Get suburb count for this LGA
                suburbs_results = await db.search_by_lga(
                    lga['lga_name'],
                    lga['state']
                )
                unique_suburbs = set(r['locality'] for r in suburbs_results)
                lga_info['suburb_count'] = len(unique_suburbs)
                lga_info['postcode_count'] = len(set(r['postcode'] for r in suburbs_results))
            
            lga_list.append(lga_info)
        
        # Sort by LGA name
        lga_list.sort(key=lambda x: x['lga_name'])
        
        # Group by state for better organization
        lgas_by_state = {}
        for lga in lga_list:
            state_code = lga['state']
            if state_code not in lgas_by_state:
                lgas_by_state[state_code] = []
            lgas_by_state[state_code].append(lga)
        
        response = {
            "status": "success",
            "total_lgas": len(lga_list),
            "lgas": lga_list
        }
        
        if not state:
            response["lgas_by_state"] = lgas_by_state
        
        response["validation_notes"] = [
            f"Found {len(lga_list)} Local Government Area(s)"
        ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing LGAs: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def search_by_region(
    region: str,
    state: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for suburbs by region name (broader than LGA).
    
    Args:
        region: Region name (e.g., "Hunter", "Illawarra")
        state: Optional state filter
        
    Returns:
        Suburbs and postcodes in the region
    """
    try:
        region = region.strip()
        
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
        
        # Search in region field
        async with db.get_connection() as conn:
            query = """
                SELECT DISTINCT 
                    postcode, locality, state, latitude, longitude,
                    lga_name, region, electoral_division
                FROM postcodes
                WHERE LOWER(region) LIKE LOWER(?)
            """
            params = [f"%{region}%"]
            
            if state:
                query += " AND state = ?"
                params.append(state)
            
            query += " ORDER BY locality, postcode"
            
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        
        if not results:
            # Try SA3/SA4 names as alternative region definitions
            async with db.get_connection() as conn:
                query = """
                    SELECT DISTINCT 
                        postcode, locality, state, latitude, longitude,
                        lga_name, region, sa3_name, sa4_name, electoral_division
                    FROM postcodes
                    WHERE LOWER(sa3_name) LIKE LOWER(?)
                        OR LOWER(sa4_name) LIKE LOWER(?)
                """
                params = [f"%{region}%", f"%{region}%"]
                
                if state:
                    query += " AND state = ?"
                    params.append(state)
                
                query += " ORDER BY locality, postcode"
                
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]
        
        if not results:
            return {
                "status": "error",
                "error": f"No region found matching '{region}'",
                "suggestion": "Try a different region name or check spelling"
            }
        
        # Group by suburb
        suburbs_dict = {}
        regions_found = set()
        for result in results:
            suburb = result['locality']
            if suburb not in suburbs_dict:
                suburbs_dict[suburb] = {
                    "suburb": suburb,
                    "postcodes": set(),
                    "state": result['state'],
                    "lga_name": result.get('lga_name'),
                    "region": result.get('region')
                }
            suburbs_dict[suburb]["postcodes"].add(result['postcode'])
            
            # Collect unique region names
            if result.get('region'):
                regions_found.add(result['region'])
            if result.get('sa3_name'):
                regions_found.add(result['sa3_name'])
            if result.get('sa4_name'):
                regions_found.add(result['sa4_name'])
        
        # Convert to list
        suburbs_list = []
        for suburb_data in suburbs_dict.values():
            suburbs_list.append({
                "suburb": suburb_data["suburb"],
                "postcodes": sorted(list(suburb_data["postcodes"])),
                "state": suburb_data["state"],
                "lga_name": suburb_data["lga_name"],
                "region": suburb_data["region"]
            })
        
        # Sort by suburb name
        suburbs_list.sort(key=lambda x: x["suburb"])
        
        return {
            "status": "success",
            "query": region,
            "regions_found": sorted(list(regions_found)),
            "suburbs": suburbs_list,
            "suburb_count": len(suburbs_list),
            "total_postcodes": len(set(r['postcode'] for r in results)),
            "validation_notes": [
                f"Found {len(suburbs_list)} suburb(s) in region matching '{region}'"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching by region: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def health_check() -> Dict[str, Any]:
    """
    Perform health check on the database and service.
    
    Returns:
        Health status and diagnostics
    """
    try:
        db = await get_database()
        
        # Check database connection
        try:
            stats = await db.get_statistics()
            db_status = "healthy"
            db_message = f"Database contains {stats['total_records']} records"
        except Exception as db_error:
            db_status = "unhealthy"
            db_message = str(db_error)
            stats = None
        
        # Check if database has data
        data_status = "healthy" if stats and stats['total_records'] > 0 else "no_data"
        
        # Build health report
        health_report = {
            "status": "success" if db_status == "healthy" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": {
                    "status": db_status,
                    "message": db_message
                },
                "data": {
                    "status": data_status,
                    "records": stats.get('total_records', 0) if stats else 0,
                    "postcodes": stats.get('unique_postcodes', 0) if stats else 0,
                    "suburbs": stats.get('unique_suburbs', 0) if stats else 0,
                    "lgas": stats.get('unique_lgas', 0) if stats else 0
                }
            }
        }
        
        if stats:
            # Add state coverage
            states_covered = list(stats.get('by_state', {}).keys())
            health_report["components"]["coverage"] = {
                "states": sorted(states_covered),
                "state_count": len(states_covered),
                "all_states_covered": len(states_covered) == len(Config.STATES)
            }
        
        # Check database file
        if Config.DATABASE_PATH.exists():
            size_mb = Config.DATABASE_PATH.stat().st_size / (1024 * 1024)
            health_report["components"]["database"]["size_mb"] = round(size_mb, 2)
        
        # Overall health
        if db_status == "healthy" and data_status == "healthy":
            health_report["health"] = "healthy"
            health_report["message"] = "All systems operational"
        elif db_status == "healthy" and data_status == "no_data":
            health_report["health"] = "needs_data"
            health_report["message"] = "Database is empty, run data loader"
        else:
            health_report["health"] = "unhealthy"
            health_report["message"] = "System experiencing issues"
        
        return health_report
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "health": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "message": "Health check failed"
        }