import logging
from abc import ABC

from app.core.supabase import get_supabase


class BasePipelineStepService(ABC):
    """Base service for all pipeline step operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_supabase(self):
        return await get_supabase()
