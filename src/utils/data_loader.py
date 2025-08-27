#!/usr/bin/env python3
"""Data loader for Australian Postcodes database."""

import sys
import asyncio
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any
import httpx
from metaphone import doublemetaphone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import Database
from src.utils.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataLoader:
    """Load postcode data into database."""
    
    def __init__(self):
        """Initialize data loader."""
        self.database = Database()
        Config.ensure_directories()
    
    async def download_data(self) -> Path:
        """Download CSV data from GitHub."""
        csv_path = Config.DATA_DIR / "postcodes.csv"
        
        logger.info(f"Downloading data from {Config.DATA_URL}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(Config.DATA_URL)
            response.raise_for_status()
            
            with open(csv_path, 'wb') as f:
                f.write(response.content)
        
        logger.info(f"Downloaded data to {csv_path}")
        return csv_path
    
    def parse_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Parse CSV file and extract relevant fields."""
        records = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Extract and clean data
                record = {
                    'postcode': row.get('postcode', '').strip(),
                    'locality': row.get('locality', '').strip(),
                    'state': row.get('state', '').strip().upper(),
                    'longitude': self._parse_float(row.get('long') or row.get('Long_precise')),
                    'latitude': self._parse_float(row.get('lat') or row.get('Lat_precise')),
                    'lga_name': row.get('lgaregion', '').strip() or None,
                    'lga_code': row.get('lgacode', '').strip() or None,
                    'sa3_name': row.get('sa3name', '').strip() or None,
                    'sa3_code': row.get('sa3', '').strip() or None,
                    'sa4_name': row.get('sa4name', '').strip() or None,
                    'sa4_code': row.get('sa4', '').strip() or None,
                    'region': row.get('region', '').strip() or None,
                    'electoral_division': row.get('electorate', '').strip() or None,
                    'altitude': self._parse_int(row.get('altitude')),
                    'phn_name': row.get('phn_name', '').strip() or None,
                    'phn_code': row.get('phn_code', '').strip() or None,
                }
                
                # Skip records without essential fields
                if record['postcode'] and record['locality'] and record['state']:
                    records.append(record)
        
        logger.info(f"Parsed {len(records)} records from CSV")
        return records
    
    def _parse_float(self, value: str) -> float:
        """Parse float value from string."""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_int(self, value: str) -> int:
        """Parse int value from string."""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    async def load_data(self, records: List[Dict[str, Any]]):
        """Load records into database."""
        await self.database.init_schema()
        
        async with self.database.get_connection() as conn:
            # Clear existing data
            await conn.execute("DELETE FROM postcodes")
            await conn.execute("DELETE FROM phonetic_codes")
            
            # Insert postcodes
            insert_query = """
                INSERT OR IGNORE INTO postcodes (
                    postcode, locality, state, longitude, latitude,
                    lga_name, lga_code, sa3_name, sa3_code,
                    sa4_name, sa4_code, region, electoral_division,
                    altitude, phn_name, phn_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Batch insert
            batch_size = 500
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                await conn.executemany(insert_query, [
                    (
                        r['postcode'], r['locality'], r['state'],
                        r['longitude'], r['latitude'],
                        r['lga_name'], r['lga_code'],
                        r['sa3_name'], r['sa3_code'],
                        r['sa4_name'], r['sa4_code'],
                        r['region'], r['electoral_division'],
                        r['altitude'], r['phn_name'], r['phn_code']
                    )
                    for r in batch
                ])
                
                if (i + batch_size) % 2000 == 0:
                    logger.info(f"Inserted {min(i + batch_size, len(records))} records")
            
            await conn.commit()
            logger.info("All postcodes inserted")
            
            # Generate phonetic codes
            await self._generate_phonetic_codes(conn, records)
            
            # Update FTS index
            await conn.execute("""
                INSERT INTO postcodes_fts(locality, state, lga_name)
                SELECT locality, state, lga_name FROM postcodes
            """)
            
            await conn.commit()
            logger.info("FTS index updated")
    
    async def _generate_phonetic_codes(self, conn, records: List[Dict[str, Any]]):
        """Generate phonetic codes for fuzzy matching."""
        logger.info("Generating phonetic codes...")
        
        # Get unique locality-state combinations
        unique_localities = {}
        for record in records:
            key = (record['locality'], record['state'])
            if key not in unique_localities:
                unique_localities[key] = True
        
        # Generate phonetic codes
        phonetic_query = """
            INSERT OR IGNORE INTO phonetic_codes (
                locality, state, primary_code, secondary_code
            ) VALUES (?, ?, ?, ?)
        """
        
        phonetic_records = []
        for (locality, state) in unique_localities.keys():
            primary, secondary = doublemetaphone(locality)
            phonetic_records.append((
                locality, state,
                primary or "", secondary or ""
            ))
        
        # Batch insert
        await conn.executemany(phonetic_query, phonetic_records)
        await conn.commit()
        
        logger.info(f"Generated {len(phonetic_records)} phonetic codes")
    
    async def verify_data(self):
        """Verify loaded data."""
        stats = await self.database.get_statistics()
        
        logger.info("Database statistics:")
        logger.info(f"  Total records: {stats['total_records']}")
        logger.info(f"  Unique postcodes: {stats['unique_postcodes']}")
        logger.info(f"  Unique suburbs: {stats['unique_suburbs']}")
        logger.info(f"  Unique LGAs: {stats['unique_lgas']}")
        
        logger.info("Records by state:")
        for state, data in stats['by_state'].items():
            logger.info(f"  {state}: {data['postcodes']} postcodes, {data['suburbs']} suburbs")
    
    async def run(self, update: bool = False):
        """Run the data loading process."""
        try:
            # Check if database exists and has data
            if not update and Config.DATABASE_PATH.exists():
                stats = await self.database.get_statistics()
                if stats['total_records'] > 0:
                    logger.info(f"Database already contains {stats['total_records']} records")
                    logger.info("Use --update flag to force update")
                    return
            
            # Download data
            csv_path = await self.download_data()
            
            # Parse CSV
            records = self.parse_csv(csv_path)
            
            # Load into database
            await self.load_data(records)
            
            # Verify
            await self.verify_data()
            
            logger.info("Data loading completed successfully!")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
        finally:
            await self.database.disconnect()

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load Australian Postcodes data")
    parser.add_argument('--update', action='store_true', help='Force update existing data')
    args = parser.parse_args()
    
    loader = DataLoader()
    await loader.run(update=args.update)

if __name__ == "__main__":
    asyncio.run(main())