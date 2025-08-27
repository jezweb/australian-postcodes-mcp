#!/usr/bin/env python3
"""
Local test script for Australian Postcodes MCP Server
Run this to test the server locally before deployment
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools import (
    search_by_postcode,
    search_by_suburb,
    find_similar_suburbs,
    list_suburbs_in_lga,
    get_state_statistics,
    health_check
)

async def run_tests():
    """Run basic tests to verify functionality."""
    print("=" * 60)
    print("Australian Postcodes MCP Server - Local Tests")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Health Check:")
    health = await health_check()
    print(f"   Status: {health.get('health', 'unknown')}")
    print(f"   Records: {health.get('components', {}).get('data', {}).get('records', 0)}")
    
    # Test 2: Search by postcode
    print("\n2. Search by Postcode (2000):")
    result = await search_by_postcode("2000")
    if result['status'] == 'success':
        print(f"   Found {result['count']} suburb(s)")
        for suburb in result['suburbs'][:3]:
            print(f"   - {suburb['locality']}, {suburb['state']}")
    
    # Test 3: Search by suburb
    print("\n3. Search by Suburb (Newcastle, NSW):")
    result = await search_by_suburb("Newcastle", "NSW")
    if result['status'] == 'success':
        print(f"   Postcodes: {', '.join(result['postcodes'])}")
    
    # Test 4: Fuzzy matching
    print("\n4. Fuzzy Match (Sydny):")
    result = await find_similar_suburbs("Sydny")
    if result['status'] == 'success':
        if result.get('primary_result'):
            print(f"   Did you mean: {result['primary_result']['suburb']}?")
            print(f"   Confidence: {result['confidence']:.2f}")
    
    # Test 5: LGA search
    print("\n5. Suburbs in LGA (Newcastle):")
    result = await list_suburbs_in_lga("Newcastle")
    if result['status'] == 'success':
        print(f"   Found {result['suburb_count']} suburb(s)")
        print(f"   Sample suburbs: {', '.join([s['suburb'] for s in result['suburbs'][:5]])}")
    
    # Test 6: State statistics
    print("\n6. State Statistics (NSW):")
    result = await get_state_statistics("NSW")
    if result['status'] == 'success':
        stats = result.get('statistics', {})
        print(f"   Postcodes: {stats.get('total_postcodes', 0)}")
        print(f"   Suburbs: {stats.get('total_suburbs', 0)}")
        print(f"   LGAs: {stats.get('total_lgas', 0)}")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())