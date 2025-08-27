"""Tools for Australian Postcodes MCP Server."""

from .search_tools import (
    search_by_postcode,
    search_by_suburb,
    validate_suburb_postcode,
    get_location_details
)

from .validation_tools import (
    find_similar_suburbs,
    autocomplete_suburb,
    validate_spelling,
    phonetic_search
)

from .location_tools import (
    list_suburbs_in_lga,
    find_lga_for_suburb,
    list_suburbs_in_radius,
    get_neighboring_suburbs
)

from .analytics_tools import (
    get_state_statistics,
    list_all_lgas,
    search_by_region,
    health_check
)

__all__ = [
    # Search tools
    'search_by_postcode',
    'search_by_suburb',
    'validate_suburb_postcode',
    'get_location_details',
    
    # Validation tools
    'find_similar_suburbs',
    'autocomplete_suburb',
    'validate_spelling',
    'phonetic_search',
    
    # Location tools
    'list_suburbs_in_lga',
    'find_lga_for_suburb',
    'list_suburbs_in_radius',
    'get_neighboring_suburbs',
    
    # Analytics tools
    'get_state_statistics',
    'list_all_lgas',
    'search_by_region',
    'health_check'
]