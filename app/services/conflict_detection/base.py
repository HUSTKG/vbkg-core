import logging
from abc import ABC
from dataclasses import dataclass
from typing import Optional

from app.core.supabase import get_supabase


@dataclass
class IncrementalConflictConfig:
    """Configuration for incremental conflict detection"""

    batch_size: int = 100
    similarity_threshold: float = 0.85
    temporal_window_hours: int = 24
    enable_llm_resolution: bool = True
    confidence_threshold: float = 0.8
    max_conflicts_per_batch: int = 50


class BaseConflictService(ABC):
    """Base service for all conflict detection operations"""

    def __init__(self, config: Optional[IncrementalConflictConfig] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or IncrementalConflictConfig()

    async def get_supabase(self):
        return await get_supabase()
