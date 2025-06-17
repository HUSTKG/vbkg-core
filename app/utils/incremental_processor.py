import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


class IncrementalStrategy(str, Enum):
    """Incremental processing strategies"""
    TIMESTAMP = "timestamp"
    SEQUENCE = "sequence"
    HASH = "hash"
    CUSTOM = "custom"
    FILE_MODIFICATION = "file_modification"
    EVENT_LOG = "event_log"


class ChangeType(str, Enum):
    """Types of data changes"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"
    MODIFY = "modify"


@dataclass
class IncrementalCheckpoint:
    """Incremental processing checkpoint"""
    step_id: str
    pipeline_id: str
    strategy: IncrementalStrategy
    checkpoint_field: str
    checkpoint_value: Union[str, int, float, datetime]
    last_processed: datetime
    record_count: int = 0
    hash_value: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ChangeRecord:
    """Record of a data change"""
    change_id: str
    change_type: ChangeType
    entity_id: Optional[str]
    field_name: Optional[str]
    old_value: Any
    new_value: Any
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = None


class IncrementalProcessor:
    """
    Utility class for incremental processing across different tasks
    """

    def __init__(self):
        pass

    async def initialize_incremental_processing(
        self, step_id: str, pipeline_id: str, incremental_config: Dict[str, Any]
    ) -> Optional[IncrementalCheckpoint]:
        """Initialize incremental processing for a step"""
        try:
            if not incremental_config.get("enabled", False):
                return None

            strategy = IncrementalStrategy(
                incremental_config.get("strategy", "timestamp")
            )
            checkpoint_field = incremental_config.get("checkpoint_field", "updated_at")

            # Get existing checkpoint
            existing_checkpoint = await self._get_checkpoint(step_id, pipeline_id)

            if existing_checkpoint:
                return existing_checkpoint

            # Create new checkpoint
            checkpoint = IncrementalCheckpoint(
                step_id=step_id,
                pipeline_id=pipeline_id,
                strategy=strategy,
                checkpoint_field=checkpoint_field,
                checkpoint_value=incremental_config.get(
                    "checkpoint_value", self._get_initial_checkpoint_value(strategy)
                ),
                last_processed=datetime.now(timezone.utc),
                metadata=incremental_config,
            )

            await self._store_checkpoint(checkpoint)
            return checkpoint

        except Exception as e:
            logger.error(f"Error initializing incremental processing: {e}")
            return None

    async def process_incremental_data(
        self,
        step_id: str,
        pipeline_id: str,
        input_data: Dict[str, Any],
        incremental_config: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[IncrementalCheckpoint]]:
        """Process data incrementally based on checkpoint"""
        try:
            checkpoint = await self.initialize_incremental_processing(
                step_id, pipeline_id, incremental_config
            )

            if not checkpoint:
                return input_data, None

            # Filter data based on checkpoint
            filtered_data = await self._filter_incremental_data(input_data, checkpoint)

            # Update checkpoint if data was processed
            if self._has_new_data(filtered_data):
                new_checkpoint_value = await self._calculate_new_checkpoint(
                    filtered_data, checkpoint
                )

                if new_checkpoint_value:
                    checkpoint.checkpoint_value = new_checkpoint_value
                    checkpoint.last_processed = datetime.now(timezone.utc)
                    checkpoint.record_count += self._count_records(filtered_data)

                    await self._update_checkpoint(checkpoint)

            return filtered_data, checkpoint

        except Exception as e:
            logger.error(f"Error processing incremental data: {e}")
            return input_data, None

    async def detect_changes(
        self,
        step_id: str,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None,
    ) -> List[ChangeRecord]:
        """Detect changes between current and previous data"""
        try:
            changes = []

            if not previous_data:
                # All data is new
                for key, value in current_data.items():
                    if isinstance(value, (list, dict)) and value:
                        change = ChangeRecord(
                            change_id=str(uuid4()),
                            change_type=ChangeType.INSERT,
                            entity_id=key,
                            field_name=None,
                            old_value=None,
                            new_value=value,
                            timestamp=datetime.now(timezone.utc),
                            source=step_id,
                            metadata={"data_type": type(value).__name__},
                        )
                        changes.append(change)
                return changes

            # Compare current with previous
            all_keys = set(current_data.keys()) | set(previous_data.keys())

            for key in all_keys:
                current_value = current_data.get(key)
                previous_value = previous_data.get(key)

                if key not in previous_data:
                    # New entity
                    change = ChangeRecord(
                        change_id=str(uuid4()),
                        change_type=ChangeType.INSERT,
                        entity_id=key,
                        field_name=None,
                        old_value=None,
                        new_value=current_value,
                        timestamp=datetime.now(timezone.utc),
                        source=step_id,
                    )
                    changes.append(change)

                elif key not in current_data:
                    # Deleted entity
                    change = ChangeRecord(
                        change_id=str(uuid4()),
                        change_type=ChangeType.DELETE,
                        entity_id=key,
                        field_name=None,
                        old_value=previous_value,
                        new_value=None,
                        timestamp=datetime.now(timezone.utc),
                        source=step_id,
                    )
                    changes.append(change)

                elif current_value != previous_value:
                    # Modified entity
                    if isinstance(current_value, dict) and isinstance(previous_value, dict):
                        # Detailed field-level comparison
                        field_changes = self._compare_dict_fields(
                            key, current_value, previous_value, step_id
                        )
                        changes.extend(field_changes)
                    else:
                        # Simple value change
                        change = ChangeRecord(
                            change_id=str(uuid4()),
                            change_type=ChangeType.UPDATE,
                            entity_id=key,
                            field_name=None,
                            old_value=previous_value,
                            new_value=current_value,
                            timestamp=datetime.now(timezone.utc),
                            source=step_id,
                        )
                        changes.append(change)

            # Store changes
            await self._store_changes(changes)
            return changes

        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            return []

    def _compare_dict_fields(
        self,
        entity_id: str,
        current_dict: Dict[str, Any],
        previous_dict: Dict[str, Any],
        source: str,
    ) -> List[ChangeRecord]:
        """Compare dictionary fields for detailed change tracking"""
        changes = []
        all_fields = set(current_dict.keys()) | set(previous_dict.keys())

        for field in all_fields:
            current_value = current_dict.get(field)
            previous_value = previous_dict.get(field)

            if field not in previous_dict:
                change_type = ChangeType.INSERT
            elif field not in current_dict:
                change_type = ChangeType.DELETE
            elif current_value != previous_value:
                change_type = ChangeType.UPDATE
            else:
                continue

            change = ChangeRecord(
                change_id=str(uuid4()),
                change_type=change_type,
                entity_id=entity_id,
                field_name=field,
                old_value=previous_value,
                new_value=current_value,
                timestamp=datetime.now(timezone.utc),
                source=source,
            )
            changes.append(change)

        return changes

    async def _filter_incremental_data(
        self, input_data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Dict[str, Any]:
        """Filter data based on incremental checkpoint"""
        try:
            if checkpoint.strategy == IncrementalStrategy.TIMESTAMP:
                return await self._filter_by_timestamp(input_data, checkpoint)
            elif checkpoint.strategy == IncrementalStrategy.SEQUENCE:
                return await self._filter_by_sequence(input_data, checkpoint)
            elif checkpoint.strategy == IncrementalStrategy.HASH:
                return await self._filter_by_hash(input_data, checkpoint)
            elif checkpoint.strategy == IncrementalStrategy.FILE_MODIFICATION:
                return await self._filter_by_file_modification(input_data, checkpoint)
            else:
                return input_data

        except Exception as e:
            logger.error(f"Error filtering incremental data: {e}")
            return input_data

    async def _filter_by_timestamp(
        self, input_data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Dict[str, Any]:
        """Filter data by timestamp"""
        filtered_data = {}
        checkpoint_value = checkpoint.checkpoint_value

        if isinstance(checkpoint_value, str):
            checkpoint_dt = datetime.fromisoformat(
                checkpoint_value.replace("Z", "+00:00")
            )
        elif isinstance(checkpoint_value, datetime):
            checkpoint_dt = checkpoint_value
        else:
            return input_data

        # Handle different data formats
        if "entities" in input_data:
            filtered_entities = []
            for entity in input_data["entities"]:
                if isinstance(entity, dict) and checkpoint.checkpoint_field in entity:
                    entity_time_str = str(entity[checkpoint.checkpoint_field])
                    try:
                        entity_time = datetime.fromisoformat(
                            entity_time_str.replace("Z", "+00:00")
                        )
                        if entity_time > checkpoint_dt:
                            filtered_entities.append(entity)
                    except:
                        filtered_entities.append(entity)  # Include if can't parse

            if filtered_entities:
                filtered_data = input_data.copy()
                filtered_data["entities"] = filtered_entities

        elif "relationships" in input_data:
            filtered_relationships = []
            for rel in input_data["relationships"]:
                if isinstance(rel, dict) and checkpoint.checkpoint_field in rel:
                    rel_time_str = str(rel[checkpoint.checkpoint_field])
                    try:
                        rel_time = datetime.fromisoformat(
                            rel_time_str.replace("Z", "+00:00")
                        )
                        if rel_time > checkpoint_dt:
                            filtered_relationships.append(rel)
                    except:
                        filtered_relationships.append(rel)

            if filtered_relationships:
                filtered_data = input_data.copy()
                filtered_data["relationships"] = filtered_relationships

        else:
            # Default to returning all data if format not recognized
            filtered_data = input_data

        return filtered_data

    async def _filter_by_sequence(
        self, input_data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Dict[str, Any]:
        """Filter data by sequence number"""
        filtered_data = {}
        checkpoint_value = checkpoint.checkpoint_value

        try:
            checkpoint_seq = int(checkpoint_value)
        except (ValueError, TypeError):
            return input_data

        # Handle entities
        if "entities" in input_data:
            filtered_entities = []
            for entity in input_data["entities"]:
                if isinstance(entity, dict) and checkpoint.checkpoint_field in entity:
                    try:
                        entity_seq = int(entity[checkpoint.checkpoint_field])
                        if entity_seq > checkpoint_seq:
                            filtered_entities.append(entity)
                    except (ValueError, TypeError):
                        filtered_entities.append(entity)

            if filtered_entities:
                filtered_data = input_data.copy()
                filtered_data["entities"] = filtered_entities

        return filtered_data

    async def _filter_by_hash(
        self, input_data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Dict[str, Any]:
        """Filter data by hash comparison"""
        current_hash = self._calculate_data_hash(input_data)

        if current_hash != checkpoint.hash_value:
            checkpoint.hash_value = current_hash
            return input_data
        else:
            return {}  # No changes

    async def _filter_by_file_modification(
        self, input_data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Dict[str, Any]:
        """Filter data by file modification time"""
        filtered_data = {}

        if "files" in input_data:
            filtered_files = []
            checkpoint_time = checkpoint.checkpoint_value

            if isinstance(checkpoint_time, str):
                checkpoint_dt = datetime.fromisoformat(
                    checkpoint_time.replace("Z", "+00:00")
                )
            elif isinstance(checkpoint_time, datetime):
                checkpoint_dt = checkpoint_time
            else:
                return input_data

            for file_data in input_data["files"]:
                if isinstance(file_data, dict) and "data" in file_data:
                    metadata = file_data["data"].get("metadata", {})
                    modified_time_str = metadata.get("modified_time")

                    if modified_time_str:
                        try:
                            modified_time = datetime.fromisoformat(
                                modified_time_str.replace("Z", "+00:00")
                            )
                            if modified_time > checkpoint_dt:
                                filtered_files.append(file_data)
                        except:
                            filtered_files.append(file_data)

            if filtered_files:
                filtered_data = input_data.copy()
                filtered_data["files"] = filtered_files

        return filtered_data

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of data for change detection"""
        try:
            # Create deterministic string representation
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception:
            return str(hash(str(data)))

    def _has_new_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains new records"""
        if not data:
            return False

        # Check different data formats
        if "entities" in data:
            return len(data["entities"]) > 0
        elif "relationships" in data:
            return len(data["relationships"]) > 0
        elif "files" in data:
            return len(data["files"]) > 0

        return bool(data)

    def _count_records(self, data: Dict[str, Any]) -> int:
        """Count records in data"""
        try:
            if "entities" in data:
                return len(data["entities"])
            elif "relationships" in data:
                return len(data["relationships"])
            elif "files" in data:
                return len(data["files"])
            else:
                return 1 if data else 0
        except Exception:
            return 0

    async def _calculate_new_checkpoint(
        self, data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Optional[Union[str, int, datetime]]:
        """Calculate new checkpoint value from processed data"""
        try:
            if checkpoint.strategy == IncrementalStrategy.TIMESTAMP:
                return self._get_max_timestamp(data, checkpoint.checkpoint_field)
            elif checkpoint.strategy == IncrementalStrategy.SEQUENCE:
                return self._get_max_sequence(data, checkpoint.checkpoint_field)
            elif checkpoint.strategy == IncrementalStrategy.FILE_MODIFICATION:
                return self._get_max_file_modification_time(data)
            elif checkpoint.strategy == IncrementalStrategy.HASH:
                return self._calculate_data_hash(data)

            return None

        except Exception as e:
            logger.error(f"Error calculating new checkpoint: {e}")
            return None

    def _get_max_timestamp(
        self, data: Dict[str, Any], field_name: str
    ) -> Optional[str]:
        """Get maximum timestamp from data"""
        max_timestamp = None

        try:
            records = []

            if "entities" in data:
                records = data["entities"]
            elif "relationships" in data:
                records = data["relationships"]

            for record in records:
                if isinstance(record, dict) and field_name in record:
                    timestamp_str = str(record[field_name])
                    if not max_timestamp or timestamp_str > max_timestamp:
                        max_timestamp = timestamp_str

            return max_timestamp

        except Exception:
            return None

    def _get_max_sequence(self, data: Dict[str, Any], field_name: str) -> Optional[int]:
        """Get maximum sequence number from data"""
        max_sequence = None

        try:
            records = []

            if "entities" in data:
                records = data["entities"]
            elif "relationships" in data:
                records = data["relationships"]

            for record in records:
                if isinstance(record, dict) and field_name in record:
                    try:
                        sequence = int(record[field_name])
                        if max_sequence is None or sequence > max_sequence:
                            max_sequence = sequence
                    except (ValueError, TypeError):
                        continue

            return max_sequence

        except Exception:
            return None

    def _get_max_file_modification_time(self, data: Dict[str, Any]) -> Optional[str]:
        """Get maximum file modification time"""
        max_time = None

        try:
            if "files" in data:
                for file_data in data["files"]:
                    if isinstance(file_data, dict) and "data" in file_data:
                        metadata = file_data["data"].get("metadata", {})
                        modified_time = metadata.get("modified_time")

                        if modified_time and (not max_time or modified_time > max_time):
                            max_time = modified_time

            return max_time

        except Exception:
            return None

    def _get_initial_checkpoint_value(
        self, strategy: IncrementalStrategy
    ) -> Union[str, int]:
        """Get initial checkpoint value for strategy"""
        if strategy == IncrementalStrategy.TIMESTAMP:
            return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        elif strategy == IncrementalStrategy.SEQUENCE:
            return 0
        elif strategy == IncrementalStrategy.FILE_MODIFICATION:
            return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        else:
            return ""

    async def _get_checkpoint(
        self, step_id: str, pipeline_id: str
    ) -> Optional[IncrementalCheckpoint]:
        """Get existing checkpoint from database"""
        try:
            supabase = await get_supabase()

            response = (
                await supabase.from_("incremental_checkpoints")
                .select("*")
                .eq("step_id", step_id)
                .eq("pipeline_id", pipeline_id)
                .maybe_single()
                .execute()
            )

            if response.data:
                data = response.data
                checkpoint = IncrementalCheckpoint(
                    step_id=data["step_id"],
                    pipeline_id=data["pipeline_id"],
                    strategy=IncrementalStrategy(data["strategy"]),
                    checkpoint_field=data["checkpoint_field"],
                    checkpoint_value=data["checkpoint_value"],
                    last_processed=datetime.fromisoformat(data["last_processed"]),
                    record_count=data.get("record_count", 0),
                    hash_value=data.get("hash_value"),
                    metadata=(
                        json.loads(data["metadata"]) if data.get("metadata") else {}
                    ),
                )
                return checkpoint

            return None

        except Exception as e:
            logger.error(f"Error getting checkpoint: {e}")
            return None

    async def _store_checkpoint(self, checkpoint: IncrementalCheckpoint):
        """Store checkpoint in database"""
        try:
            supabase = await get_supabase()

            checkpoint_data = {
                "step_id": checkpoint.step_id,
                "pipeline_id": checkpoint.pipeline_id,
                "strategy": checkpoint.strategy.value,
                "checkpoint_field": checkpoint.checkpoint_field,
                "checkpoint_value": checkpoint.checkpoint_value,
                "last_processed": checkpoint.last_processed.isoformat(),
                "record_count": checkpoint.record_count,
                "hash_value": checkpoint.hash_value,
                "metadata": (
                    json.dumps(checkpoint.metadata) if checkpoint.metadata else None
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            await supabase.from_("incremental_checkpoints").insert(
                checkpoint_data
            ).execute()

        except Exception as e:
            logger.error(f"Error storing checkpoint: {e}")

    async def _update_checkpoint(self, checkpoint: IncrementalCheckpoint):
        """Update existing checkpoint"""
        try:
            supabase = await get_supabase()

            update_data = {
                "checkpoint_value": checkpoint.checkpoint_value,
                "last_processed": checkpoint.last_processed.isoformat(),
                "record_count": checkpoint.record_count,
                "hash_value": checkpoint.hash_value,
                "metadata": (
                    json.dumps(checkpoint.metadata) if checkpoint.metadata else None
                ),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            await supabase.from_("incremental_checkpoints").update(update_data).eq(
                "step_id", checkpoint.step_id
            ).eq("pipeline_id", checkpoint.pipeline_id).execute()

        except Exception as e:
            logger.error(f"Error updating checkpoint: {e}")

    async def _store_changes(self, changes: List[ChangeRecord]):
        """Store change records in database"""
        try:
            if not changes:
                return

            supabase = await get_supabase()

            change_data = []
            for change in changes:
                data = {
                    "change_id": change.change_id,
                    "change_type": change.change_type.value,
                    "entity_id": change.entity_id,
                    "field_name": change.field_name,
                    "old_value": (
                        json.dumps(change.old_value)
                        if change.old_value is not None
                        else None
                    ),
                    "new_value": (
                        json.dumps(change.new_value)
                        if change.new_value is not None
                        else None
                    ),
                    "timestamp": change.timestamp.isoformat(),
                    "source": change.source,
                    "metadata": (
                        json.dumps(change.metadata) if change.metadata else None
                    ),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                change_data.append(data)

            await supabase.from_("change_records").insert(change_data).execute()

        except Exception as e:
            logger.error(f"Error storing changes: {e}")


# Create global incremental processor instance
incremental_processor = IncrementalProcessor()
