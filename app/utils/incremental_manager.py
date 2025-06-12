import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
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


@dataclass
class ProvenanceRecord:
    """Data provenance record"""

    entity_id: str
    step_id: str
    pipeline_run_id: str
    source_system: str
    source_record_id: Optional[str]
    transformation_applied: List[str]
    quality_score: float
    confidence_score: float
    timestamp: datetime
    lineage: List[str] = None
    metadata: Dict[str, Any] = None


class IncrementalProcessingManager:
    """Manages incremental processing across pipeline steps"""

    def __init__(self):
        self.checkpoints = {}
        self.change_log = []

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
                    if isinstance(current_value, dict) and isinstance(
                        previous_value, dict
                    ):
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
        if "database_result" in input_data:
            db_data = input_data["database_result"]
            if "data" in db_data and "data" in db_data["data"]:
                records = db_data["data"]["data"]
                filtered_records = []

                for record in records:
                    if (
                        isinstance(record, dict)
                        and checkpoint.checkpoint_field in record
                    ):
                        record_time_str = str(record[checkpoint.checkpoint_field])
                        try:
                            record_time = datetime.fromisoformat(
                                record_time_str.replace("Z", "+00:00")
                            )
                            if record_time > checkpoint_dt:
                                filtered_records.append(record)
                        except:
                            filtered_records.append(record)  # Include if can't parse

                if filtered_records:
                    filtered_data = input_data.copy()
                    filtered_data["database_result"]["data"]["data"] = filtered_records

        elif "api_response" in input_data:
            api_data = input_data["api_response"]
            if "data" in api_data and isinstance(api_data["data"]["data"], list):
                records = api_data["data"]["data"]
                filtered_records = []

                for record in records:
                    if (
                        isinstance(record, dict)
                        and checkpoint.checkpoint_field in record
                    ):
                        record_time_str = str(record[checkpoint.checkpoint_field])
                        try:
                            record_time = datetime.fromisoformat(
                                record_time_str.replace("Z", "+00:00")
                            )
                            if record_time > checkpoint_dt:
                                filtered_records.append(record)
                        except:
                            filtered_records.append(record)

                if filtered_records:
                    filtered_data = input_data.copy()
                    filtered_data["api_response"]["data"]["data"] = filtered_records

        else:
            # Default to returning all data if format not recognized
            filtered_data = input_data

        return filtered_data

    async def _filter_by_sequence(
        self, input_data: Dict[str, Any], checkpoint: IncrementalCheckpoint
    ) -> Dict[str, Any]:
        """Filter data by sequence number"""
        # Similar implementation to timestamp but comparing sequence numbers
        return input_data  # Placeholder

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
        if "database_result" in data:
            return len(data["database_result"].get("data", {}).get("data", [])) > 0
        elif "api_response" in data:
            return len(data["api_response"].get("data", {}).get("data", [])) > 0
        elif "files" in data:
            return len(data["files"]) > 0

        return bool(data)

    def _count_records(self, data: Dict[str, Any]) -> int:
        """Count records in data"""
        try:
            if "database_result" in data:
                return len(data["database_result"].get("data", {}).get("data", []))
            elif "api_response" in data:
                api_data = data["api_response"].get("data", {}).get("data", [])
                return len(api_data) if isinstance(api_data, list) else 1
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

            if "database_result" in data:
                records = data["database_result"].get("data", {}).get("data", [])
            elif "api_response" in data:
                api_data = data["api_response"].get("data", {}).get("data", [])
                records = api_data if isinstance(api_data, list) else [api_data]

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

            if "database_result" in data:
                records = data["database_result"].get("data", {}).get("data", [])
            elif "api_response" in data:
                api_data = data["api_response"].get("data", {}).get("data", [])
                records = api_data if isinstance(api_data, list) else [api_data]

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


class ProvenanceManager:
    """Manages data provenance and lineage tracking"""

    def __init__(self):
        self.provenance_cache = {}

    async def track_provenance(
        self,
        entity_id: str,
        step_id: str,
        pipeline_run_id: str,
        source_system: str,
        transformation_applied: List[str],
        quality_score: float = 0.8,
        confidence_score: float = 0.8,
        source_record_id: Optional[str] = None,
        lineage: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRecord:
        """Track provenance for an entity"""
        try:
            provenance = ProvenanceRecord(
                entity_id=entity_id,
                step_id=step_id,
                pipeline_run_id=pipeline_run_id,
                source_system=source_system,
                source_record_id=source_record_id,
                transformation_applied=transformation_applied,
                quality_score=quality_score,
                confidence_score=confidence_score,
                timestamp=datetime.now(timezone.utc),
                lineage=lineage or [],
                metadata=metadata or {},
            )

            await self._store_provenance(provenance)
            return provenance

        except Exception as e:
            logger.error(f"Error tracking provenance: {e}")
            return None

    async def get_entity_lineage(self, entity_id: str) -> List[ProvenanceRecord]:
        """Get complete lineage for an entity"""
        try:
            supabase = await get_supabase()

            response = (
                await supabase.from_("provenance_records")
                .select("*")
                .eq("entity_id", entity_id)
                .order("timestamp")
                .execute()
            )

            lineage = []
            for data in response.data:
                provenance = ProvenanceRecord(
                    entity_id=data["entity_id"],
                    step_id=data["step_id"],
                    pipeline_run_id=data["pipeline_run_id"],
                    source_system=data["source_system"],
                    source_record_id=data["source_record_id"],
                    transformation_applied=(
                        json.loads(data["transformation_applied"])
                        if data["transformation_applied"]
                        else []
                    ),
                    quality_score=data["quality_score"],
                    confidence_score=data["confidence_score"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    lineage=json.loads(data["lineage"]) if data["lineage"] else [],
                    metadata=json.loads(data["metadata"]) if data["metadata"] else {},
                )
                lineage.append(provenance)

            return lineage

        except Exception as e:
            logger.error(f"Error getting entity lineage: {e}")
            return []

    async def _store_provenance(self, provenance: ProvenanceRecord):
        """Store provenance record in database"""
        try:
            supabase = await get_supabase()

            provenance_data = {
                "entity_id": provenance.entity_id,
                "step_id": provenance.step_id,
                "pipeline_run_id": provenance.pipeline_run_id,
                "source_system": provenance.source_system,
                "source_record_id": provenance.source_record_id,
                "transformation_applied": json.dumps(provenance.transformation_applied),
                "quality_score": provenance.quality_score,
                "confidence_score": provenance.confidence_score,
                "timestamp": provenance.timestamp.isoformat(),
                "lineage": json.dumps(provenance.lineage),
                "metadata": json.dumps(provenance.metadata),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            await supabase.from_("provenance_records").insert(provenance_data).execute()

        except Exception as e:
            logger.error(f"Error storing provenance: {e}")


# Initialize global managers
incremental_manager = IncrementalProcessingManager()
provenance_manager = ProvenanceManager()
