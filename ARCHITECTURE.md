# Architecture Documentation

## System Overview

The Australian Postcodes MCP Server is a FastMCP-based service that provides intelligent postcode and suburb data access with fuzzy matching capabilities. It's designed for AI assistants handling customer service interactions where address validation and correction are critical.

## Architecture Principles

1. **Modular Design**: Separate concerns into distinct modules (tools, database, utilities)
2. **Performance First**: SQLite with optimized indexes for sub-100ms responses
3. **AI-Optimized**: Structured responses with confidence scoring and alternatives
4. **Fault Tolerant**: Graceful handling of misspellings and ambiguous inputs
5. **Maintainable**: Clear separation of business logic and data access

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Clients                         │
│            (Claude, ChatGPT, Custom AI Apps)            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   FastMCP Server                        │
│                    (server.py)                          │
├─────────────────────────────────────────────────────────┤
│  • Request Router                                       │
│  • JSON-RPC Handler                                     │
│  • Response Formatter                                   │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Search Tools │   │ Validation   │   │ Location     │
│              │   │    Tools     │   │   Tools      │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ • Postcode   │   │ • Fuzzy      │   │ • LGA Query  │
│ • Suburb     │   │   Matching   │   │ • Radius     │
│ • Smart      │   │ • Phonetic   │   │ • Neighbors  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Database Layer                        │
│                    (database.py)                        │
├─────────────────────────────────────────────────────────┤
│  • Connection Pool                                      │
│  • Query Builder                                        │
│  • Index Management                                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    SQLite Database                      │
│                   (postcodes.db)                        │
├─────────────────────────────────────────────────────────┤
│  Tables: postcodes                                      │
│  Indexes: postcode, locality, state, lga_name          │
│  FTS5: locality_fts for fuzzy search                   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Processing Pipeline

1. **Request Reception**
   - MCP client sends JSON-RPC request
   - FastMCP validates request structure
   - Routes to appropriate tool handler

2. **Tool Execution**
   - Tool validates parameters
   - Constructs database query
   - Applies fuzzy matching if needed
   - Formats response with metadata

3. **Response Construction**
   - Primary result with confidence score
   - Alternative suggestions if applicable
   - Validation notes and warnings
   - Structured JSON response

### Example Flow: Fuzzy Search

```
User Input: "Newcaslte NSW"
    │
    ▼
Validation Tool (find_similar_suburbs)
    │
    ├─> Exact Match Check
    │   └─> Not found
    │
    ├─> Fuzzy Match (rapidfuzz)
    │   ├─> Newcastle (0.92)
    │   ├─> New Lambton (0.75)
    │   └─> Newstead (0.68)
    │
    ├─> Phonetic Match (Metaphone)
    │   └─> Newcastle
    │
    └─> Response
        {
          "exact_match": false,
          "confidence": 0.92,
          "primary_result": {
            "suburb": "Newcastle",
            "state": "NSW",
            "postcode": "2300"
          },
          "alternatives": [...],
          "suggestion": "Did you mean 'Newcastle' in NSW?"
        }
```

## Database Schema

### Primary Table: postcodes

```sql
CREATE TABLE postcodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    postcode TEXT NOT NULL,
    locality TEXT NOT NULL,
    state TEXT NOT NULL,
    longitude REAL,
    latitude REAL,
    lga_name TEXT,
    lga_code TEXT,
    sa3_name TEXT,
    sa3_code TEXT,
    sa4_name TEXT,
    sa4_code TEXT,
    region TEXT,
    electoral_division TEXT,
    altitude INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_postcode ON postcodes(postcode);
CREATE INDEX idx_locality ON postcodes(locality);
CREATE INDEX idx_state ON postcodes(state);
CREATE INDEX idx_lga_name ON postcodes(lga_name);
CREATE INDEX idx_locality_state ON postcodes(locality, state);
```

### Full-Text Search Table

```sql
CREATE VIRTUAL TABLE postcodes_fts USING fts5(
    locality,
    content=postcodes,
    content_rowid=id
);
```

## Module Structure

### Core Modules

#### server.py
- FastMCP server initialization
- Tool registration
- Lifecycle management
- Error handling

#### database.py
- SQLite connection management
- Query execution
- Connection pooling
- Transaction handling

### Tool Modules

#### search_tools.py
- Basic postcode/suburb lookups
- Smart search with type detection
- Validation of combinations

#### validation_tools.py
- Fuzzy string matching (Levenshtein)
- Phonetic matching (Soundex/Metaphone)
- Autocomplete functionality
- Spelling correction

#### location_tools.py
- LGA (Local Government Area) queries
- Geographic radius searches
- Neighbor detection
- Distance calculations

#### analytics_tools.py
- State statistics
- Regional analysis
- Data coverage reports

### Utility Modules

#### config.py
- Environment variable management
- Default configurations
- Feature flags

#### fuzzy_match.py
- String similarity algorithms
- Phonetic encoding
- Abbreviation expansion

#### data_loader.py
- CSV parsing
- Data validation
- Database population
- Update mechanisms

## Performance Optimizations

### Database Optimizations
1. **Indexed Columns**: All frequently queried fields
2. **Composite Indexes**: For multi-field queries
3. **FTS5**: For fuzzy text search
4. **Connection Pool**: Reuse database connections
5. **Prepared Statements**: Compiled query plans

### Algorithm Optimizations
1. **Cached Phonetic Codes**: Pre-compute for all suburbs
2. **Tiered Matching**: Exact → Fuzzy → Phonetic
3. **Early Termination**: Stop on high-confidence matches
4. **Batch Processing**: Multiple queries in single DB round-trip

### Response Optimizations
1. **Lazy Loading**: Only compute alternatives if needed
2. **Result Limiting**: Cap number of suggestions
3. **Confidence Threshold**: Filter low-quality matches

## Security Considerations

### Input Validation
- Parameter type checking
- SQL injection prevention via parameterized queries
- Input length limits
- Character sanitization

### Data Protection
- Read-only database access for queries
- No PII storage
- Audit logging for updates

### API Security
- Rate limiting (handled by FastMCP)
- Request validation
- Error message sanitization

## Scalability Considerations

### Current Design (SQLite)
- Suitable for read-heavy workloads
- ~17,000 records easily handled
- Sub-100ms query performance
- Single-file deployment

### Future Scaling Options
1. **PostgreSQL Migration**
   - For concurrent writes
   - Better full-text search
   - Spatial queries with PostGIS

2. **Caching Layer**
   - Redis for frequent queries
   - In-memory suburb cache
   - Computed similarity matrix

3. **Distributed Deployment**
   - Read replicas
   - Geographic distribution
   - Load balancing

## Testing Strategy

### Unit Tests
- Individual tool functions
- Fuzzy matching algorithms
- Database operations

### Integration Tests
- End-to-end MCP requests
- Database interactions
- Error scenarios

### Performance Tests
- Query response times
- Concurrent request handling
- Memory usage

### Accuracy Tests
- Fuzzy match quality
- Phonetic match accuracy
- LGA boundary correctness

## Monitoring and Observability

### Metrics
- Query response times
- Match confidence distribution
- Error rates by tool
- Popular queries

### Logging
- Request/response pairs
- Fuzzy match decisions
- Performance bottlenecks
- Error details

### Health Checks
- Database connectivity
- Data freshness
- Memory usage
- Response time SLA

## Maintenance and Updates

### Data Updates
- Weekly sync from GitHub source
- Validation of new data
- Incremental updates
- Rollback capability

### Schema Evolution
- Migration scripts
- Backward compatibility
- Version tracking

### Dependency Management
- Regular security updates
- Compatibility testing
- Version pinning

## Deployment Architecture

### FastMCP Cloud (Production)
```
GitHub Repository
    │
    ▼
FastMCP Cloud Platform
    │
    ├─> Build Process
    │   └─> Dependency Installation
    │
    ├─> Deployment
    │   └─> Server Instances
    │
    └─> Runtime
        ├─> Environment Variables
        ├─> SQLite Database
        └─> MCP Endpoint
```

### Local Development
```
Local Repository
    │
    ├─> Virtual Environment
    ├─> SQLite Database
    └─> FastMCP Dev Server
```

## Future Enhancements

1. **Machine Learning**
   - Learn from correction patterns
   - Improve fuzzy match scoring
   - Predict likely queries

2. **Extended Data**
   - Business postcodes
   - PO Box ranges
   - Historical postcodes

3. **Advanced Geography**
   - Drive time calculations
   - Public transport routes
   - Service area mapping

4. **Multi-language Support**
   - Suburb name translations
   - Phonetic matching for accents