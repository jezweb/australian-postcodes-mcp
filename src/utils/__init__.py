"""Utility modules for Australian Postcodes MCP Server."""

from .config import Config
from .fuzzy_match import (
    calculate_similarity,
    phonetic_encode,
    find_best_matches,
    expand_abbreviations
)

__all__ = [
    'Config',
    'calculate_similarity',
    'phonetic_encode', 
    'find_best_matches',
    'expand_abbreviations'
]