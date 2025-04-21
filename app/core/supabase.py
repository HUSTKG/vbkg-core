from typing import Optional
import logging
import os
from supabase._async.client import AsyncClient as Client, create_client

from app.core.config import settings

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None

async def get_supabase() -> Client:
    """
    Get or create a Supabase client instance.
    
    Returns:
        Supabase Client instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = await create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info(f"Connected to Supabase at {settings.SUPABASE_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    return _supabase_client

async def test_supabase_connection() -> bool:
    """
    Test the Supabase connection.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        supabase = await get_supabase()
        
        # Try a simple query to check connection
        response = await supabase.table("roles").select("*").limit(1).execute()
        
        if response.data is not None:
            logger.info("Supabase connection test successful")
            return True
        else:
            logger.error("Supabase connection test failed")
            return False
    
    except Exception as e:
        logger.error(f"Supabase connection test error: {e}")
        return False
