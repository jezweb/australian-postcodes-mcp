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
│   ├── search_tools.py    # Basic lookups ✓
│   ├── validation_tools.py # Fuzzy matching ✓
│   ├── location_tools.py  # Geographic queries (in progress)
│   └── analytics_tools.py # Statistics
└── utils/
    ├── config.py       # Configuration ✓
    ├── fuzzy_match.py  # Matching utilities ✓
    └── data_loader.py  # CSV import ✓
```

## Progress Notes

### 2025-08-27 - Initial Setup
- ✓ Created project structure
- ✓ Set up comprehensive documentation (README, ARCHITECTURE, CLAUDE, DEPLOYMENT, CHANGELOG)
- ✓ Implemented configuration management
- ✓ Created fuzzy matching utilities with phonetic support
- ✓ Built database module with async SQLite
- ✓ Created data loader for CSV import
- ✓ Implemented search tools (postcode/suburb lookup)
- ✓ Implemented validation tools (fuzzy matching, autocomplete, phonetic)
- Working on: location tools, analytics tools, main server

## Current Status
- Database schema ready with FTS5 support
- Core search and validation tools complete
- Need to:
  1. Complete location tools (LGA, radius search)
  2. Add analytics tools
  3. Create main FastMCP server
  4. Test data import
  5. Deploy to GitHub and FastMCP Cloud

## Testing Checklist
- [x] Basic postcode lookup logic
- [x] Suburb search with state filter
- [x] Fuzzy matching implementation
- [x] Phonetic matching implementation
- [ ] LGA queries
- [ ] Geographic radius search
- [ ] Data import from CSV
- [ ] Performance with full dataset
- [ ] FastMCP server integration
- [ ] FastMCP Cloud deployment

## Known Challenges
1. Handling suburbs with same name in different states - SOLVED with state filter
2. Common abbreviations (Mt/Mount, St/Saint) - SOLVED with expansion
3. Phonetic variations (Newcastle vs New Castle) - SOLVED with compound word handling
4. Multiple postcodes for same suburb - HANDLED in results

## API Response Structure
Consistent across all tools:
```json
{
  "status": "success|error",
  "exact_match": true|false,
  "confidence": 0.0-1.0,
  "primary_result": {...},
  "alternatives": [...],
  "suggestion": "Human-readable suggestion",
  "validation_notes": ["List of validation checks"]
}
```

## Deployment Notes
- Use FastMCP Cloud for hosting
- Environment variables for configuration
- GitHub repo: australian-postcodes-mcp
- Regular updates from source data

## Next Steps
1. Complete location_tools.py (LGA, radius search)
2. Create analytics_tools.py (statistics, health check)
3. Build main server.py with FastMCP
4. Test data import
5. Create GitHub repository
6. Deploy to FastMCP Cloud