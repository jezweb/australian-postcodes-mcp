#!/usr/bin/env python3
"""
Australian Postcodes MCP Server
Fast, comprehensive postcode and suburb lookup service for Australia
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
import structlog

# Import all tools
from tools import (
    # Search tools
    search_by_postcode,
    search_by_suburb,
    validate_suburb_postcode,
    get_location_details,
    
    # Validation tools
    find_similar_suburbs,
    autocomplete_suburb,
    validate_spelling,
    phonetic_search,
    
    # Location tools
    list_suburbs_in_lga,
    find_lga_for_suburb,
    list_suburbs_in_radius,
    get_neighboring_suburbs,
    
    # Analytics tools
    get_state_statistics,
    list_all_lgas,
    search_by_region,
    health_check
)

from utils.config import Config
from utils.data_loader import DataLoader
from database import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastMCP server instance
mcp = FastMCP(
    name="australian-postcodes",
    version="1.0.0"
)

# Server metadata
mcp.add_metadata({
    "description": "Comprehensive Australian postcodes and suburbs lookup service",
    "author": "Jezweb",
    "contact": "jeremy@jezweb.net",
    "capabilities": [
        "Postcode to suburb lookup",
        "Suburb to postcode lookup",
        "Fuzzy matching for misspelled suburbs",
        "Phonetic search for voice input",
        "Local Government Area (LGA) queries",
        "Geographic radius search",
        "Autocomplete suggestions",
        "State-based statistics"
    ],
    "data_source": "https://github.com/matthewproctor/australianpostcodes",
    "total_records": "~17,000 postcode-suburb combinations",
    "coverage": "All Australian states and territories"
})

# ============================================================================
# SEARCH TOOLS
# ============================================================================

@mcp.tool(
    description="Find all suburbs for a given postcode",
    examples=[
        {"postcode": "2000"},
        {"postcode": "3141"}
    ]
)
async def search_postcode(postcode: str) -> Dict[str, Any]:
    """Find suburbs by postcode (4 digits)."""
    logger.info("search_postcode", postcode=postcode)
    return await search_by_postcode(postcode)

@mcp.tool(
    description="Find postcodes for a suburb name",
    examples=[
        {"suburb": "Newcastle", "state": "NSW"},
        {"suburb": "Richmond"},
        {"suburb": "Surry Hills", "state": "NSW"}
    ]
)
async def search_suburb(suburb: str, state: str = None) -> Dict[str, Any]:
    """Find postcodes by suburb name with optional state filter."""
    logger.info("search_suburb", suburb=suburb, state=state)
    return await search_by_suburb(suburb, state)

@mcp.tool(
    description="Validate if a suburb-postcode combination is correct",
    examples=[
        {"suburb": "Sydney", "postcode": "2000"},
        {"suburb": "Melbourne", "postcode": "3000", "state": "VIC"}
    ]
)
async def validate_combination(
    suburb: str,
    postcode: str,
    state: str = None
) -> Dict[str, Any]:
    """Check if suburb and postcode match."""
    logger.info("validate_combination", suburb=suburb, postcode=postcode, state=state)
    return await validate_suburb_postcode(suburb, postcode, state)

@mcp.tool(
    description="Smart search accepting either postcode or suburb name",
    examples=[
        {"query": "2000"},
        {"query": "Newcastle"},
        {"query": "Brisbane, QLD"}
    ]
)
async def smart_search(query: str) -> Dict[str, Any]:
    """Intelligent search that detects query type."""
    logger.info("smart_search", query=query)
    return await get_location_details(query)

# ============================================================================
# VALIDATION & FUZZY MATCHING TOOLS
# ============================================================================

@mcp.tool(
    description="Find similar suburbs for possibly misspelled names",
    examples=[
        {"misspelled": "Sydny"},
        {"misspelled": "Melborn", "state": "VIC"},
        {"misspelled": "New Castle", "threshold": 0.8}
    ]
)
async def fuzzy_match_suburb(
    misspelled: str,
    state: str = None,
    threshold: float = None
) -> Dict[str, Any]:
    """Find similar suburbs using fuzzy matching."""
    logger.info("fuzzy_match_suburb", misspelled=misspelled, state=state, threshold=threshold)
    return await find_similar_suburbs(misspelled, state, threshold)

@mcp.tool(
    description="Get autocomplete suggestions for partial suburb names",
    examples=[
        {"partial": "Syd"},
        {"partial": "Mel", "state": "VIC"},
        {"partial": "Bris", "limit": 5}
    ]
)
async def autocomplete(
    partial: str,
    state: str = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Provide autocomplete suggestions."""
    logger.info("autocomplete", partial=partial, state=state, limit=limit)
    return await autocomplete_suburb(partial, state, limit)

@mcp.tool(
    description="Check spelling and suggest corrections for suburbs",
    examples=[
        {"suburb": "Sydny"},
        {"suburb": "Brisben"}
    ]
)
async def check_spelling(suburb: str) -> Dict[str, Any]:
    """Validate suburb spelling and suggest corrections."""
    logger.info("check_spelling", suburb=suburb)
    return await validate_spelling(suburb)

@mcp.tool(
    description="Search suburbs by phonetic similarity (for voice input)",
    examples=[
        {"spoken_name": "New Castle"},
        {"spoken_name": "Saint Kilda"},
        {"spoken_name": "Wooloomooloo"}
    ]
)
async def voice_search(spoken_name: str) -> Dict[str, Any]:
    """Find suburbs based on how they sound."""
    logger.info("voice_search", spoken_name=spoken_name)
    return await phonetic_search(spoken_name)

# ============================================================================
# LOCATION & LGA TOOLS
# ============================================================================

@mcp.tool(
    description="List all suburbs in a Local Government Area (city/council)",
    examples=[
        {"lga_name": "Newcastle"},
        {"lga_name": "Sydney", "state": "NSW"},
        {"lga_name": "Brisbane"}
    ]
)
async def suburbs_in_lga(
    lga_name: str,
    state: str = None
) -> Dict[str, Any]:
    """Get all suburbs in an LGA/city."""
    logger.info("suburbs_in_lga", lga_name=lga_name, state=state)
    return await list_suburbs_in_lga(lga_name, state)

@mcp.tool(
    description="Find the LGA (city/council) for a suburb",
    examples=[
        {"suburb": "Bondi Beach"},
        {"suburb": "St Kilda", "state": "VIC"}
    ]
)
async def get_suburb_lga(
    suburb: str,
    state: str = None
) -> Dict[str, Any]:
    """Find which LGA a suburb belongs to."""
    logger.info("get_suburb_lga", suburb=suburb, state=state)
    return await find_lga_for_suburb(suburb, state)

@mcp.tool(
    description="Find suburbs within radius of a location",
    examples=[
        {"postcode_or_suburb": "2000", "radius_km": 5},
        {"postcode_or_suburb": "Melbourne", "radius_km": 10, "state": "VIC"}
    ]
)
async def suburbs_within_radius(
    postcode_or_suburb: str,
    radius_km: float,
    state: str = None
) -> Dict[str, Any]:
    """Search suburbs within geographic radius."""
    logger.info("suburbs_within_radius", 
                postcode_or_suburb=postcode_or_suburb, 
                radius_km=radius_km, 
                state=state)
    return await list_suburbs_in_radius(postcode_or_suburb, radius_km, state)

@mcp.tool(
    description="Find neighboring suburbs (adjacent areas)",
    examples=[
        {"suburb": "Bondi"},
        {"suburb": "Richmond", "state": "VIC", "max_neighbors": 5}
    ]
)
async def find_neighbors(
    suburb: str,
    state: str = None,
    max_neighbors: int = 10
) -> Dict[str, Any]:
    """Get neighboring suburbs."""
    logger.info("find_neighbors", suburb=suburb, state=state, max_neighbors=max_neighbors)
    return await get_neighboring_suburbs(suburb, state, max_neighbors)

# ============================================================================
# ANALYTICS & STATISTICS TOOLS
# ============================================================================

@mcp.tool(
    description="Get statistics for a state or all states",
    examples=[
        {"state": "NSW"},
        {"state": "VIC"},
        {}
    ]
)
async def state_stats(state: str = None) -> Dict[str, Any]:
    """Get comprehensive state statistics."""
    logger.info("state_stats", state=state)
    return await get_state_statistics(state)

@mcp.tool(
    description="List all Local Government Areas",
    examples=[
        {},
        {"state": "NSW"},
        {"state": "VIC", "include_suburbs_count": True}
    ]
)
async def list_lgas(
    state: str = None,
    include_suburbs_count: bool = False
) -> Dict[str, Any]:
    """Get all LGAs with optional statistics."""
    logger.info("list_lgas", state=state, include_suburbs_count=include_suburbs_count)
    return await list_all_lgas(state, include_suburbs_count)

@mcp.tool(
    description="Search suburbs by region name",
    examples=[
        {"region": "Hunter"},
        {"region": "Illawarra", "state": "NSW"},
        {"region": "Gold Coast"}
    ]
)
async def search_region(
    region: str,
    state: str = None
) -> Dict[str, Any]:
    """Find suburbs in a named region."""
    logger.info("search_region", region=region, state=state)
    return await search_by_region(region, state)

@mcp.tool(
    description="Check database and service health status",
    examples=[{}]
)
async def check_health() -> Dict[str, Any]:
    """Perform system health check."""
    logger.info("check_health")
    return await health_check()

# ============================================================================
# INITIALIZATION
# ============================================================================

async def initialize_database():
    """Initialize database on first run."""
    logger.info("Checking database initialization...")
    
    try:
        # Check if database exists and has data
        db = await get_database()
        stats = await db.get_statistics()
        
        if stats['total_records'] > 0:
            logger.info(f"Database ready with {stats['total_records']} records")
            return True
        
        # Database empty, need to load data
        logger.info("Database empty, loading data...")
        loader = DataLoader()
        await loader.run(update=False)
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for the server."""
    # Initialize database if needed
    if not await initialize_database():
        logger.error("Failed to initialize database, some features may not work")
    
    # Run the FastMCP server
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())