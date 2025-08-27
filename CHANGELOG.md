# Changelog

All notable changes to the Australian Postcodes MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and documentation
- Core MCP server implementation with FastMCP
- SQLite database for postcode storage
- Search tools for postcode and suburb lookups
- Fuzzy matching with confidence scoring
- Phonetic search for voice transcription
- LGA (Local Government Area) queries
- Geographic radius searches
- Autocomplete functionality
- Data import from GitHub CSV source
- Comprehensive documentation suite

### Security
- SQL injection prevention via parameterized queries
- Input validation and sanitization
- Read-only database access for queries

## [1.0.0] - 2025-08-27

### Added
- Initial release of Australian Postcodes MCP Server
- Complete set of search and validation tools
- ~17,000 Australian postcodes and suburbs
- FastMCP Cloud deployment support
- Docker deployment option
- Comprehensive test suite

### Features
- **Search Tools**
  - `search_by_postcode` - Find suburbs for a postcode
  - `search_by_suburb` - Find postcodes for a suburb
  - `validate_suburb_postcode` - Verify combinations
  - `get_location_details` - Smart search

- **Fuzzy Matching Tools**
  - `find_similar_suburbs` - Handle misspellings
  - `autocomplete_suburb` - Complete partial names
  - `validate_spelling` - Suggest corrections
  - `phonetic_search` - Handle voice input

- **Location Tools**
  - `list_suburbs_in_lga` - LGA queries
  - `find_lga_for_suburb` - Get city/council
  - `list_suburbs_in_radius` - Geographic search
  - `get_neighboring_suburbs` - Adjacent areas

- **Analytics Tools**
  - `get_state_statistics` - State-level stats
  - `list_all_lgas` - Available LGAs
  - `search_by_region` - Regional queries

### Documentation
- README.md with quick start guide
- ARCHITECTURE.md with system design
- CLAUDE.md with AI integration guide
- DEPLOYMENT.md with deployment options
- CHANGELOG.md for version tracking

### Performance
- Sub-100ms response time for most queries
- Optimized SQLite indexes
- Efficient fuzzy matching algorithms
- Cached phonetic encodings

---

## Development Roadmap

### [1.1.0] - Planned
- [ ] Machine learning for improved fuzzy matching
- [ ] Historical postcode support
- [ ] Business postcode categories
- [ ] PO Box range detection

### [1.2.0] - Planned
- [ ] Multi-language suburb names
- [ ] Indigenous place names
- [ ] Alternative name mappings
- [ ] Pronunciation guides

### [2.0.0] - Future
- [ ] GraphQL API support
- [ ] Real-time data updates
- [ ] Street-level data
- [ ] Routing capabilities

---

## Version History Format

### Version Numbering
- **Major (X.0.0)**: Breaking changes to API
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes and minor improvements

### Release Process
1. Update version in `src/utils/config.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v1.0.0 -m "Release version 1.0.0"`
4. Push to GitHub: `git push origin v1.0.0`
5. Deploy to FastMCP Cloud

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style guidelines

---

## Acknowledgments

- Data source: [Australian Postcodes](https://github.com/matthewproctor/australianpostcodes)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Protocol: [Model Context Protocol](https://modelcontextprotocol.io)