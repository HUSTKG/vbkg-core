from typing import Optional
import logging
import os
from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)

_driver: Optional[AsyncDriver] = None

def get_neo4j_driver() -> AsyncDriver:
    """
    Get or create a Neo4j driver instance.
    
    Returns:
        AsyncDriver instance
    """
    global _driver
    
    if _driver is None:
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            _driver = AsyncGraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
            logger.info(f"Connected to Neo4j at {neo4j_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    return _driver

async def close_neo4j_driver():
    """Close the Neo4j driver connection."""
    global _driver
    
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")

async def init_neo4j_constraints():
    """
    Initialize Neo4j constraints and indexes.
    """
    try:
        driver = get_neo4j_driver()
        
        async with driver.session() as session:
            # Create constraint on Entity nodes
            await session.run("""
                CREATE CONSTRAINT entity_id IF NOT EXISTS
                FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE
            """)
            
            # Create constraint on relationship IDs
            await session.run("""
                CREATE CONSTRAINT relationship_id IF NOT EXISTS
                FOR ()-[r]-() REQUIRE r.relationship_id IS UNIQUE
            """)
            
            # Create index on entity text for faster searches
            await session.run("""
                CREATE INDEX entity_text IF NOT EXISTS
                FOR (e:Entity) ON (e.entity_text)
            """)
            
            logger.info("Neo4j constraints and indexes initialized")
    
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j constraints: {e}")
        raise

async def test_neo4j_connection() -> bool:
    """
    Test the Neo4j connection.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        driver = get_neo4j_driver()
        
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS x")
            record = await result.single()
            
            if record and record.get("x") == 1:
                logger.info("Neo4j connection test successful")
                return True
            else:
                logger.error("Neo4j connection test failed")
                return False
    
    except Exception as e:
        logger.error(f"Neo4j connection test error: {e}")
        return False
