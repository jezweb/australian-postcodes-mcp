# Claude Integration Guide

This document provides guidance for Claude (and other AI assistants) on how to effectively use the Australian Postcodes MCP Server.

## Overview

This MCP server is specifically designed to help AI assistants handle Australian address-related queries with high accuracy, even when dealing with misspellings, phonetic variations, or ambiguous inputs.

## Key Capabilities

### What This Server Does Well
- ✅ Validates Australian postcodes and suburbs
- ✅ Corrects misspelled suburb names
- ✅ Handles phonetic variations (voice transcription)
- ✅ Finds suburbs within Local Government Areas (cities)
- ✅ Provides geographic proximity searches
- ✅ Offers confidence scores for fuzzy matches
- ✅ Suggests alternatives when uncertain

### What This Server Doesn't Do
- ❌ Street-level address validation
- ❌ International postcodes
- ❌ Routing or directions
- ❌ Real-time updates (data updated weekly)

## Usage Patterns

### Basic Address Validation

When a user provides an address, use these tools in sequence:

1. **First, try exact match:**
   ```
   validate_suburb_postcode("Newcastle", "2300")
   ```

2. **If no match, try fuzzy search:**
   ```
   find_similar_suburbs("Newcaslte", state="NSW")
   ```

3. **For voice input, use phonetic search:**
   ```
   phonetic_search("new castle")
   ```

### Handling Ambiguous Input

When the user provides partial information:

```python
# User says: "I'm in Newcastle"
# Problem: Multiple Newcastles exist in Australia

# Step 1: Search without state
results = search_by_suburb("Newcastle")

# Step 2: If multiple results, ask for clarification
"I found Newcastle in NSW (2300) and Newcastle in VIC (3875). 
 Which state are you in?"

# Step 3: Once clarified, get full details
details = get_location_details("Newcastle NSW")
```

### Customer Service Scenarios

#### Scenario 1: Booking Confirmation
```python
# Customer: "I'm at 2300... uh, Newcastle West I think?"

# Validate the combination
result = validate_suburb_postcode("Newcastle West", "2300")

# Response structure:
{
  "valid": true,
  "confidence": 1.0,
  "details": {
    "suburb": "Newcastle West",
    "postcode": "2300",
    "state": "NSW",
    "lga": "Newcastle"
  }
}
```

#### Scenario 2: Service Area Check
```python
# Customer: "Do you service the Newcastle area?"

# Get all suburbs in the LGA
suburbs = list_suburbs_in_lga("Newcastle", "NSW")

# Or check radius from a point
nearby = list_suburbs_in_radius(
  lat=-32.9283,
  lon=151.7817,
  radius_km=10
)
```

#### Scenario 3: Spelling Correction
```python
# Customer: "I live in Cambelltown" (missing 'p')

# Find similar suburbs
matches = find_similar_suburbs("Cambelltown", state="NSW")

# Returns:
{
  "exact_match": false,
  "suggestions": [
    {"suburb": "Campbelltown", "confidence": 0.95},
    {"suburb": "Camberwell", "confidence": 0.70}
  ],
  "best_match": "Campbelltown"
}
```

## Best Practices

### 1. Always Provide Context

When searching, include state if known:
```python
# Good
search_by_suburb("Richmond", state="VIC")

# Less optimal (returns multiple states)
search_by_suburb("Richmond")
```

### 2. Use Confidence Scores

Interpret confidence scores appropriately:
- `> 0.95`: Almost certainly correct
- `0.85 - 0.95`: Likely correct, confirm with user
- `0.70 - 0.85`: Possible match, show alternatives
- `< 0.70`: Uncertain, ask for clarification

### 3. Handle Multiple Results

Many suburbs exist in multiple states:
```python
# Common duplicates:
# - Richmond (NSW, VIC, QLD, TAS, SA)
# - Springfield (QLD, NSW, VIC, SA)
# - Newtown (NSW, VIC, QLD, TAS)

# Always clarify state when ambiguous
```

### 4. Phonetic Variations

Common voice transcription issues:
```python
# Mount/Mt variations
phonetic_search("mount druitt")  # Finds "Mt Druitt"

# Saint/St variations  
phonetic_search("saint kilda")   # Finds "St Kilda"

# Compound words
phonetic_search("new castle")    # Finds "Newcastle"
phonetic_search("spring field")   # Finds "Springfield"
```

### 5. Autocomplete for Partial Input

Help users complete suburb names:
```python
# User types: "Param"
suggestions = autocomplete_suburb("Param", state="NSW")

# Returns:
["Parramatta", "Parafield", "Paramatta Park"]
```

## Response Interpretation

### Understanding Response Structure

All tools return structured responses with:

```python
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

### Error Handling

Common error scenarios and responses:

```python
# No matches found
{
  "status": "error",
  "error": "No suburbs found matching 'Xyzcity'",
  "suggestion": "Please check the spelling or try a nearby suburb"
}

# Multiple exact matches (need state)
{
  "status": "success",
  "exact_match": true,
  "multiple_results": true,
  "results": [...],
  "suggestion": "Multiple suburbs found. Please specify the state."
}
```

## Tool Selection Guide

| User Query | Recommended Tool | Why |
|------------|-----------------|-----|
| "What's the postcode for Newcastle?" | `search_by_suburb()` | Direct suburb to postcode lookup |
| "What suburbs are in 2300?" | `search_by_postcode()` | Direct postcode to suburbs lookup |
| "Is Newcaslte 2300 correct?" | `find_similar_suburbs()` then `validate_suburb_postcode()` | Handle typo first, then validate |
| "What suburbs are in Newcastle council?" | `list_suburbs_in_lga()` | LGA-based query |
| "I said New Castle on the phone" | `phonetic_search()` | Voice transcription issue |
| "Suburbs near Parramatta?" | `list_suburbs_in_radius()` | Geographic proximity |
| "Is it Cambelltown or Campbelltown?" | `validate_spelling()` | Spelling verification |

## Performance Tips

1. **Cache Common Queries**: Remember frequently asked postcodes during conversation
2. **Batch Similar Requests**: If validating multiple addresses, prepare them together
3. **Use Smart Search**: `get_location_details()` auto-detects input type
4. **Limit Alternatives**: Don't overwhelm users with too many suggestions

## Common Australian Address Quirks

### Special Cases to Remember

1. **ACT Postcodes**: Often start with 26 or 29
2. **PO Boxes**: Have different postcodes from street addresses
3. **New Developments**: Database might not have latest suburbs
4. **Rural Areas**: Large postcodes covering multiple localities
5. **State Borders**: Some postcodes span state boundaries

### Abbreviation Conventions

Common abbreviations in Australian addresses:
- Mt = Mount
- St = Saint/Street (context dependent)
- Pt = Port/Point
- Sth = South
- Nth = North
- Ck = Creek
- Hts = Heights

## Integration Examples

### Example 1: Address Form Validation

```python
async def validate_address_form(suburb, postcode, state):
    # Step 1: Validate the combination
    validation = await validate_suburb_postcode(suburb, postcode)
    
    if not validation['valid']:
        # Step 2: Try to fix spelling
        suggestions = await find_similar_suburbs(suburb, state)
        
        if suggestions['confidence'] > 0.9:
            # High confidence correction
            return {
                "corrected": True,
                "suggestion": suggestions['best_match'],
                "message": f"Did you mean {suggestions['best_match']}?"
            }
        else:
            # Low confidence, need user input
            return {
                "corrected": False,
                "alternatives": suggestions['suggestions'],
                "message": "Please select the correct suburb"
            }
    
    return {"valid": True, "message": "Address validated successfully"}
```

### Example 2: Service Area Checker

```python
async def check_service_area(customer_location, service_areas):
    # Get customer's LGA
    location = await get_location_details(customer_location)
    customer_lga = location['lga_name']
    
    # Check if LGA is serviced
    if customer_lga in service_areas:
        return {"serviced": True, "area": customer_lga}
    
    # Check nearby areas
    nearby = await list_suburbs_in_radius(
        location['latitude'],
        location['longitude'], 
        10  # 10km radius
    )
    
    for suburb in nearby:
        if suburb['lga_name'] in service_areas:
            return {
                "serviced": True,
                "area": suburb['lga_name'],
                "note": "Nearby service area available"
            }
    
    return {"serviced": False}
```

## Troubleshooting

### Issue: Too Many Results
**Solution**: Always include state parameter when possible

### Issue: No Matches for Valid Suburb
**Solution**: Check for abbreviations (Mt/Mount) or try phonetic search

### Issue: Confidence Too Low
**Solution**: Ask user for additional context (state, nearby suburbs)

### Issue: Slow Response
**Solution**: Use more specific queries, avoid wildcard searches

## Updates and Maintenance

- Data is updated weekly from the source repository
- New suburbs are added as they become available
- Historical postcodes are retained for reference
- Report issues via GitHub repository