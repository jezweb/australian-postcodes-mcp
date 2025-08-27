# Australian Postcodes MCP Server - Development Scratchpad

## Project Overview
Building a FastMCP server for Australian postcodes data to help AI assistants with address validation, fuzzy matching, and location queries.

## Data Source
- GitHub: https://github.com/matthewproctor/australianpostcodes
- CSV file: ~17,000 records
- Fields: postcode, locality, state, lat/long, LGA, SA3/SA4, etc.

## Key Requirements
1. **Phone/Chat AI Support**
   - Fuzzy matching for misspelled suburbs
   - Phonetic search for voice transcription
   - LGA (Local Government Area) queries
   - Confidence scoring

2. **Core Functionality**
   - Search by postcode → suburbs
   - Search by suburb → postcodes
   - Find suburbs in LGA/city
   - Geographic proximity search
   - Validation and suggestions

## Technical Stack
- FastMCP v2.12.0+
- SQLite for data storage
- rapidfuzz for fuzzy matching
- Python 3.9+

## Database Design
- Primary table: postcodes
- Indexes on: postcode, locality, state, lga_name
- Full-text search on locality for fuzzy matching

## Module Structure
```
src/
├── server.py           # Main FastMCP server
├── database.py         # SQLite setup and connection
├── tools/
│   ├── search_tools.py    # Basic lookups
│   ├── validation_tools.py # Fuzzy matching
│   ├── location_tools.py  # Geographic queries
│   └── analytics_tools.py # Statistics
└── utils/
    ├── config.py       # Configuration
    ├── fuzzy_match.py  # Matching utilities
    └── data_loader.py  # CSV import
```

## Progress Notes

### 2025-08-27 - Initial Setup
- Created project structure
- Setting up documentation
- Planning modular architecture

## Testing Checklist
- [ ] Basic postcode lookup
- [ ] Suburb search with typos
- [ ] LGA queries
- [ ] Geographic radius search
- [ ] Phonetic matching
- [ ] Performance with full dataset
- [ ] FastMCP Cloud deployment

## Known Challenges
1. Handling suburbs with same name in different states
2. Common abbreviations (Mt/Mount, St/Saint)
3. Phonetic variations (Newcastle vs New Castle)
4. Multiple postcodes for same suburb

## Deployment Notes
- Use FastMCP Cloud for hosting
- Environment variables for configuration
- GitHub repo: australian-postcodes-mcp
- Regular updates from source data