# Australian Postcodes MCP Server

A high-performance MCP (Model Context Protocol) server providing Australian postcode and suburb data with intelligent fuzzy matching, designed specifically for AI assistants handling customer service interactions.

## Features

### 🔍 Core Search Capabilities
- **Postcode to Suburbs**: Find all suburbs for a given postcode
- **Suburb to Postcodes**: Find postcodes for suburbs (with fuzzy matching)
- **Smart Validation**: Verify suburb-postcode combinations
- **LGA Queries**: List all suburbs in a Local Government Area (city/council)

### 🎯 AI-Optimized Features
- **Fuzzy Matching**: Handles typos and misspellings with confidence scoring
- **Phonetic Search**: Matches spoken names that may be misheard
- **Autocomplete**: Suggests completions for partial suburb names
- **Smart Suggestions**: Provides alternatives when exact matches aren't found
- **Geographic Search**: Find nearby suburbs within a radius

### 📊 Data Coverage
- ~17,000 Australian postcodes and suburbs
- Local Government Areas (LGAs)
- Statistical Areas (SA3/SA4)
- Geographic coordinates (latitude/longitude)
- Electoral divisions
- State and region information

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/australian-postcodes-mcp.git
cd australian-postcodes-mcp

# Install dependencies
pip install -r requirements.txt

# Import postcode data
python src/utils/data_loader.py

# Test locally
fastmcp dev src/server.py
```

### Usage with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "australian-postcodes": {
      "command": "fastmcp",
      "args": ["run", "/path/to/australian-postcodes-mcp/src/server.py"]
    }
  }
}
```

## Available Tools

### Search Tools
- `search_by_postcode` - Find suburbs for a postcode
- `search_by_suburb` - Find postcodes for a suburb
- `validate_suburb_postcode` - Verify a combination is valid
- `get_location_details` - Smart search accepting either postcode or suburb

### Fuzzy Matching Tools
- `find_similar_suburbs` - Find closest matches for misspelled suburbs
- `autocomplete_suburb` - Get completions for partial names
- `validate_spelling` - Suggest spelling corrections
- `phonetic_search` - Handle phone-misheard names

### Location Tools
- `list_suburbs_in_lga` - All suburbs in a Local Government Area
- `find_lga_for_suburb` - Get the LGA/city for a suburb
- `list_suburbs_in_radius` - Find nearby postcodes within radius
- `get_neighboring_suburbs` - Find adjacent areas

### Analytics Tools
- `get_state_statistics` - Postcode and suburb counts by state
- `list_all_lgas` - Available Local Government Areas
- `search_by_region` - Query by statistical area

## Examples

### Basic Search
```python
# Find suburbs for postcode 2300
result = await search_by_postcode("2300")
# Returns: Newcastle, Newcastle West, etc.

# Find postcode for suburb
result = await search_by_suburb("Newcastle", state="NSW")
# Returns: 2300
```

### Fuzzy Matching
```python
# Handle misspellings
result = await find_similar_suburbs("Newcaslte", state="NSW")
# Returns: Newcastle (confidence: 0.92), New Lambton (confidence: 0.75)

# Phonetic search
result = await phonetic_search("new castle")
# Returns: Newcastle, Newcastle West
```

### LGA Queries
```python
# List suburbs in Newcastle LGA
result = await list_suburbs_in_lga("Newcastle", state="NSW")
# Returns: All suburbs in Newcastle city council area
```

## Deployment

### FastMCP Cloud (Recommended)

1. Push to GitHub
2. Connect repository at [fastmcp.cloud](https://fastmcp.cloud)
3. Configure environment variables
4. Deploy with one click

### Local Development

```bash
# Run development server
fastmcp dev src/server.py

# Run production server
python src/server.py
```

## Data Source

Data sourced from the community-maintained [Australian Postcodes](https://github.com/matthewproctor/australianpostcodes) repository.

## Performance

- SQLite with optimized indexes for fast queries
- Sub-100ms response time for most queries
- Efficient fuzzy matching using rapidfuzz library
- Cached phonetic encodings for voice queries

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Support

For issues or questions, please open an issue on GitHub or contact the maintainers.

---

Built with [FastMCP](https://github.com/jlowin/fastmcp) for the [Model Context Protocol](https://modelcontextprotocol.io)