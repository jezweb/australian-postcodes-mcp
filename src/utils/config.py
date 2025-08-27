"""Configuration management for Australian Postcodes MCP Server."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration for the MCP server."""
    
    # Server Configuration
    SERVER_NAME = os.getenv("SERVER_NAME", "australian-postcodes")
    SERVER_VERSION = os.getenv("SERVER_VERSION", "1.0.0")
    SERVER_DESCRIPTION = "Australian Postcodes MCP Server with fuzzy matching"
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    DATABASE_PATH = DATA_DIR / "postcodes.db"
    
    # Data Source
    DATA_URL = os.getenv(
        "DATA_URL",
        "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/refs/heads/master/australian_postcodes.csv"
    )
    UPDATE_FREQUENCY = os.getenv("UPDATE_FREQUENCY", "weekly")
    
    # Search Configuration
    FUZZY_THRESHOLD = float(os.getenv("FUZZY_THRESHOLD", "0.8"))
    MAX_SUGGESTIONS = int(os.getenv("MAX_SUGGESTIONS", "5"))
    DEFAULT_RADIUS_KM = float(os.getenv("DEFAULT_RADIUS_KM", "10"))
    PHONETIC_THRESHOLD = float(os.getenv("PHONETIC_THRESHOLD", "0.85"))
    
    # Database Configuration
    DB_TIMEOUT = float(os.getenv("DB_TIMEOUT", "10.0"))
    DB_CHECK_SAME_THREAD = False  # Allow cross-thread access for async
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    
    # Performance
    CACHE_SIZE = int(os.getenv("CACHE_SIZE", "1000"))
    MAX_RESULTS = int(os.getenv("MAX_RESULTS", "100"))
    
    # Feature Flags
    ENABLE_PHONETIC_SEARCH = os.getenv("ENABLE_PHONETIC_SEARCH", "true").lower() == "true"
    ENABLE_FUZZY_MATCHING = os.getenv("ENABLE_FUZZY_MATCHING", "true").lower() == "true"
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
    
    # Common Australian Abbreviations
    ABBREVIATIONS = {
        "Mt": "Mount",
        "St": "Saint",
        "Pt": "Port",
        "Nth": "North",
        "Sth": "South",
        "E": "East",
        "W": "West",
        "Ck": "Creek",
        "Hts": "Heights",
        "Pk": "Park",
        "Jct": "Junction",
        "Ctr": "Centre",
        "Sq": "Square"
    }
    
    # Australian States and Territories
    STATES = {
        "NSW": "New South Wales",
        "VIC": "Victoria",
        "QLD": "Queensland",
        "SA": "South Australia",
        "WA": "Western Australia",
        "TAS": "Tasmania",
        "NT": "Northern Territory",
        "ACT": "Australian Capital Territory"
    }
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_database_url(cls):
        """Get database URL for connection."""
        return f"sqlite:///{cls.DATABASE_PATH}"
    
    @classmethod
    def is_production(cls):
        """Check if running in production mode."""
        return os.getenv("ENVIRONMENT", "development") == "production"