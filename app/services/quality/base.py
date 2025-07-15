# =============================================
# 1. BASE SERVICE & INTERFACES
# =============================================

import logging
from abc import ABC, abstractmethod

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import QualityDimension


class BaseQualityService(ABC):
    """Base service cho tất cả quality operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_supabase(self):
        return await get_supabase()


class QualityAssessor(ABC):
    """Abstract base class cho quality assessment strategies"""

    @abstractmethod
    async def assess(self, **kwargs) -> float:
        """Assess quality dimension và return score 0-1"""
        pass

    @abstractmethod
    def get_dimension(self) -> QualityDimension:
        """Return quality dimension này assess cái gì"""
        pass
