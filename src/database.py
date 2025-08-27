"""Database management for Australian Postcodes MCP Server."""

import aiosqlite
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from contextlib import asynccontextmanager

from utils.config import Config

logger = logging.getLogger(__name__)

class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager."""
        self.db_path = db_path or Config.DATABASE_PATH
        self._connection = None
    
    async def connect(self):
        """Create database connection."""
        if not self._connection:
            self._connection = await aiosqlite.connect(
                str(self.db_path),
                timeout=Config.DB_TIMEOUT,
                check_same_thread=False
            )
            # Enable optimizations
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA synchronous=NORMAL")
            await self._connection.execute("PRAGMA cache_size=10000")
    
    async def disconnect(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection context manager."""
        if not self._connection:
            await self.connect()
        try:
            yield self._connection
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
    
    async def init_schema(self):
        """Initialize database schema."""
        async with self.get_connection() as conn:
            # Main postcodes table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS postcodes (
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
                    phn_name TEXT,
                    phn_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(postcode, locality, state)
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_postcode ON postcodes(postcode)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_locality ON postcodes(locality)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON postcodes(state)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_lga_name ON postcodes(lga_name)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_locality_state ON postcodes(locality, state)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_coordinates ON postcodes(latitude, longitude)")
            
            # Phonetic codes table for faster matching
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS phonetic_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    locality TEXT NOT NULL,
                    state TEXT NOT NULL,
                    primary_code TEXT,
                    secondary_code TEXT,
                    UNIQUE(locality, state)
                )
            """)
            
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_phonetic_primary ON phonetic_codes(primary_code)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_phonetic_secondary ON phonetic_codes(secondary_code)")
            
            # Full-text search virtual table
            await conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS postcodes_fts 
                USING fts5(
                    locality,
                    state,
                    lga_name,
                    content=postcodes,
                    content_rowid=id
                )
            """)
            
            await conn.commit()
            logger.info("Database schema initialized")
    
    async def search_by_postcode(self, postcode: str) -> List[Dict[str, Any]]:
        """Search suburbs by postcode."""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT DISTINCT 
                    postcode, locality, state, latitude, longitude,
                    lga_name, region, electoral_division
                FROM postcodes
                WHERE postcode = ?
                ORDER BY locality
            """, (postcode,))
            
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def search_by_suburb(
        self, 
        suburb: str, 
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search postcodes by suburb name."""
        query = """
            SELECT DISTINCT 
                postcode, locality, state, latitude, longitude,
                lga_name, region, electoral_division
            FROM postcodes
            WHERE LOWER(locality) = LOWER(?)
        """
        params = [suburb]
        
        if state:
            query += " AND state = ?"
            params.append(state.upper())
        
        query += " ORDER BY postcode"
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def search_fuzzy(
        self,
        query: str,
        state: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fuzzy search for suburbs using FTS5."""
        fts_query = query.replace(" ", "* ") + "*"
        
        base_query = """
            SELECT DISTINCT 
                p.postcode, p.locality, p.state, p.latitude, p.longitude,
                p.lga_name, p.region, p.electoral_division
            FROM postcodes p
            INNER JOIN postcodes_fts f ON p.id = f.rowid
            WHERE postcodes_fts MATCH ?
        """
        params = [fts_query]
        
        if state:
            base_query += " AND p.state = ?"
            params.append(state.upper())
        
        base_query += " LIMIT ?"
        params.append(limit)
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(base_query, params)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def search_by_lga(
        self,
        lga_name: str,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search suburbs by Local Government Area."""
        query = """
            SELECT DISTINCT 
                postcode, locality, state, latitude, longitude,
                lga_name, region, electoral_division
            FROM postcodes
            WHERE LOWER(lga_name) LIKE LOWER(?)
        """
        params = [f"%{lga_name}%"]
        
        if state:
            query += " AND state = ?"
            params.append(state.upper())
        
        query += " ORDER BY locality, postcode"
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def search_by_radius(
        self,
        lat: float,
        lon: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Search suburbs within radius using Haversine formula."""
        # Approximate bounding box for initial filtering
        lat_range = radius_km / 111.0  # 1 degree latitude ≈ 111km
        lon_range = radius_km / (111.0 * abs(lat))  # Adjust for latitude
        
        query = """
            SELECT DISTINCT
                postcode, locality, state, latitude, longitude,
                lga_name, region, electoral_division,
                (
                    6371 * acos(
                        cos(radians(?)) * cos(radians(latitude)) *
                        cos(radians(longitude) - radians(?)) +
                        sin(radians(?)) * sin(radians(latitude))
                    )
                ) AS distance_km
            FROM postcodes
            WHERE latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                AND latitude IS NOT NULL
                AND longitude IS NOT NULL
            HAVING distance_km <= ?
            ORDER BY distance_km
        """
        
        params = [
            lat, lon, lat,  # For Haversine formula
            lat - lat_range, lat + lat_range,  # Latitude bounds
            lon - lon_range, lon + lon_range,  # Longitude bounds
            radius_km  # Final radius filter
        ]
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = [dict(zip(columns, row)) for row in rows]
            
            # Round distance for cleaner output
            for result in results:
                if 'distance_km' in result:
                    result['distance_km'] = round(result['distance_km'], 2)
            
            return results
    
    async def get_all_suburbs(self, state: Optional[str] = None) -> List[str]:
        """Get all unique suburb names."""
        query = "SELECT DISTINCT locality FROM postcodes"
        params = []
        
        if state:
            query += " WHERE state = ?"
            params.append(state.upper())
        
        query += " ORDER BY locality"
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            
            return [row[0] for row in rows]
    
    async def get_all_lgas(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all unique Local Government Areas."""
        query = """
            SELECT DISTINCT lga_name, lga_code, state
            FROM postcodes
            WHERE lga_name IS NOT NULL
        """
        params = []
        
        if state:
            query += " AND state = ?"
            params.append(state.upper())
        
        query += " ORDER BY lga_name"
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            
            return [
                {"lga_name": row[0], "lga_code": row[1], "state": row[2]}
                for row in rows
            ]
    
    async def validate_combination(
        self,
        suburb: str,
        postcode: str,
        state: Optional[str] = None
    ) -> bool:
        """Validate if suburb-postcode combination exists."""
        query = """
            SELECT COUNT(*) FROM postcodes
            WHERE LOWER(locality) = LOWER(?)
                AND postcode = ?
        """
        params = [suburb, postcode]
        
        if state:
            query += " AND state = ?"
            params.append(state.upper())
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            count = await cursor.fetchone()
            
            return count[0] > 0 if count else False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        async with self.get_connection() as conn:
            # Total records
            cursor = await conn.execute("SELECT COUNT(*) FROM postcodes")
            total = (await cursor.fetchone())[0]
            
            # By state
            cursor = await conn.execute("""
                SELECT state, COUNT(DISTINCT postcode) as postcodes, 
                       COUNT(DISTINCT locality) as suburbs
                FROM postcodes
                GROUP BY state
                ORDER BY state
            """)
            
            states = {}
            async for row in cursor:
                states[row[0]] = {
                    "postcodes": row[1],
                    "suburbs": row[2]
                }
            
            # Unique counts
            cursor = await conn.execute("""
                SELECT 
                    COUNT(DISTINCT postcode) as unique_postcodes,
                    COUNT(DISTINCT locality) as unique_suburbs,
                    COUNT(DISTINCT lga_name) as unique_lgas
                FROM postcodes
            """)
            
            unique = await cursor.fetchone()
            
            return {
                "total_records": total,
                "unique_postcodes": unique[0],
                "unique_suburbs": unique[1],
                "unique_lgas": unique[2],
                "by_state": states
            }

# Singleton instance
_database_instance = None

async def get_database() -> Database:
    """Get database singleton instance."""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
        await _database_instance.connect()
    return _database_instance