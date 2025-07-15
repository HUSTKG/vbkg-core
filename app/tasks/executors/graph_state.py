import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.schemas.conflict_resolution import ConflictStatus

logger = logging.getLogger(__name__)


class GraphDataType(Enum):
    """Types of data trong graph state"""

    RAW_TEXT = "raw_text"
    PROCESSED_CHUNKS = "processed_chunks"
    ENTITIES = "entities"
    RELATIONSHIPS = "relationships"
    CONFLICTS = "conflicts"
    RESOLUTIONS = "resolutions"
    METADATA = "metadata"


@dataclass
class GraphState:
    """Global state để maintain graph data xuyên suốt pipeline"""

    def __init__(self):
        self.entities: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self.conflicts: List[Dict[str, Any]] = []
        self.resolutions: List[Dict[str, Any]] = []
        self.raw_text_data: List[Dict[str, Any]] = []
        self.processed_chunks: List[Dict[str, Any]] = []
        self.cleaned_data: List[Dict[str, Any]] = []
        self.validation_results: Optional[Dict[str, Any]] = None
        self.metadata: Dict[str, Any] = {}
        self.step_history: List[str] = []

    def add_entities(self, new_entities: List[Dict[str, Any]], source_step: str):
        """Add hoặc merge entities from a step"""
        if new_entities:
            # Merge strategy: replace nếu có cặp text-type, add nếu mới
            existing_set = set()

            for entity in self.entities:
                existing_set.add(
                    (
                        entity.get("entity_type"),
                        entity.get("text", entity.get("entity_text")),
                    )
                )

            for entity in new_entities:
                entity_key = (
                    entity.get("entity_type"),
                    entity.get("text", entity.get("entity_text")),
                )
                if entity_key in existing_set:
                    # Update existing entity
                    for i, existing_entity in enumerate(self.entities):
                        existing_key = (
                            existing_entity.get("entity_type"),
                            existing_entity.get("text", entity.get("entity_text")),
                        )
                        if entity_key == existing_key:
                            self.entities[i] = self._merge_entity(
                                existing_entity, entity, source_step
                            )
                            break
                else:
                    # Add new entity
                    entity["_source_step"] = source_step
                    entity["_added_at"] = datetime.now(timezone.utc).isoformat()
                    self.entities.append(entity)

            logger.info(
                f"Added {len(new_entities)} entities from {source_step}. Total: {len(self.entities)}"
            )

    def add_relationships(
        self, new_relationships: List[Dict[str, Any]], source_step: str
    ):
        """Add hoặc merge relationships from a step"""
        if new_relationships:
            for relationship in new_relationships:
                relationship["_source_step"] = source_step
                relationship["_added_at"] = datetime.now(timezone.utc).isoformat()
                self.relationships.append(relationship)

            logger.info(
                f"Added {len(new_relationships)} relationships from {source_step}. Total: {len(self.relationships)}"
            )

    def add_conflicts(self, new_conflicts: List[Dict[str, Any]], source_step: str):
        """Add conflicts từ conflict detection step"""
        if new_conflicts:
            for conflict in new_conflicts:
                conflict["_source_step"] = source_step
                conflict["_added_at"] = datetime.now(timezone.utc).isoformat()
                self.conflicts.append(conflict)

            logger.info(
                f"Added {len(new_conflicts)} conflicts from {source_step}. Total: {len(self.conflicts)}"
            )

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get tất cả conflicts"""
        return self.conflicts

    def add_resolutions(self, new_resolutions: List[Dict[str, Any]], source_step: str):
        """Add resolution results from conflict resolution step"""
        if new_resolutions:
            for resolution in new_resolutions:
                resolution["_source_step"] = source_step
                resolution["_added_at"] = datetime.now(timezone.utc).isoformat()
                resolution["_graph_state_id"] = (
                    f"resolution_{len(self.resolutions) + 1}"
                )
                self.resolutions.append(resolution)

            logger.info(
                f"Added {len(new_resolutions)} resolutions from {source_step}. Total: {len(self.resolutions)}"
            )

    def update_conflict_status(
        self,
        conflict_id: str,
        new_status: str,
        resolution_data: Optional[Dict[str, Any]] = None,
    ):
        """Update status của một conflict"""
        for i, conflict in enumerate(self.conflicts):
            if (
                conflict.get("id") == conflict_id
                or conflict.get("_graph_state_id") == conflict_id
            ):

                old_status = conflict.get("status")
                conflict["status"] = new_status
                conflict["_status_updated_at"] = datetime.now(timezone.utc).isoformat()

                if resolution_data:
                    conflict["resolution_data"] = resolution_data

                logger.info(
                    f"Updated conflict {conflict_id} status: {old_status} -> {new_status}"
                )
                return True

        logger.warning(f"Conflict {conflict_id} not found for status update")
        return False

    def get_conflicts_by_status(self, status: ConflictStatus) -> List[Dict[str, Any]]:
        """Get conflicts theo status"""
        return [c for c in self.conflicts if c.get("status") == status.value]

    def get_conflicts_by_type(self, conflict_type: str) -> List[Dict[str, Any]]:
        """Get conflicts theo type"""
        return [c for c in self.conflicts if c.get("conflict_type") == conflict_type]

    def get_conflicts_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get conflicts theo severity"""
        return [c for c in self.conflicts if c.get("severity") == severity]

    def get_unresolved_conflicts(self) -> List[Dict[str, Any]]:
        """Get tất cả conflicts chưa resolved"""
        unresolved_statuses = [
            ConflictStatus.DETECTED.value,
            ConflictStatus.UNDER_REVIEW.value,
        ]
        return [c for c in self.conflicts if c.get("status") in unresolved_statuses]

    def get_resolved_conflicts(self) -> List[Dict[str, Any]]:
        """Get tất cả conflicts đã resolved"""
        resolved_statuses = [
            ConflictStatus.RESOLVED_AUTO.value,
            ConflictStatus.RESOLVED_MANUAL.value,
        ]
        return [c for c in self.conflicts if c.get("status") in resolved_statuses]

    def get_resolution_statistics(self) -> Dict[str, Any]:
        """Get thống kê về conflicts và resolutions"""
        total_conflicts = len(self.conflicts)
        if total_conflicts == 0:
            return {
                "total_conflicts": 0,
                "resolution_rate": 0.0,
                "auto_resolution_rate": 0.0,
                "manual_resolution_rate": 0.0,
            }

        resolved_conflicts = self.get_resolved_conflicts()
        auto_resolved = self.get_conflicts_by_status(ConflictStatus.RESOLVED_AUTO)
        manual_resolved = self.get_conflicts_by_status(ConflictStatus.RESOLVED_MANUAL)
        under_review = self.get_conflicts_by_status(ConflictStatus.UNDER_REVIEW)
        detected = self.get_conflicts_by_status(ConflictStatus.DETECTED)

        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": len(resolved_conflicts),
            "auto_resolved": len(auto_resolved),
            "manual_resolved": len(manual_resolved),
            "under_review": len(under_review),
            "detected": len(detected),
            "resolution_rate": len(resolved_conflicts) / total_conflicts,
            "auto_resolution_rate": len(auto_resolved) / total_conflicts,
            "manual_resolution_rate": len(manual_resolved) / total_conflicts,
            "total_resolutions": len(self.resolutions),
        }

    def store_conflict_detection_results(
        self, detection_results: Dict[str, Any], source_step: str
    ):
        """Store kết quả conflict detection vào metadata và conflicts list"""
        # Store in metadata
        self.metadata["conflict_detection"] = {
            "results": detection_results,
            "source_step": source_step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Extract individual conflicts if available
        conflicts_to_add = []

        if "detection_results" in detection_results:
            for detection_type, result in detection_results[
                "detection_results"
            ].items():
                if "conflicts_detected" in result and result["conflicts_detected"] > 0:
                    # If detailed conflicts are available, add them
                    if "detailed_conflicts" in result:
                        for conflict in result["detailed_conflicts"]:
                            conflict["detection_type"] = detection_type
                            conflicts_to_add.append(conflict)

        if conflicts_to_add:
            self.add_conflicts(conflicts_to_add, source_step)

        logger.info(f"Stored conflict detection results from {source_step}")

    def store_conflict_resolution_results(
        self, resolution_results: Dict[str, Any], source_step: str
    ):
        """Store kết quả conflict resolution vào metadata và resolutions list"""
        # Store in metadata
        self.metadata["conflict_resolution"] = {
            "results": resolution_results,
            "source_step": source_step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Process resolution details and update conflict statuses
        if "resolution_results" in resolution_results:
            for resolution_type, result in resolution_results[
                "resolution_results"
            ].items():
                if "resolution_details" in result:
                    for detail in result["resolution_details"]:
                        conflict_id = detail.get("conflict_id")
                        status = detail.get("status")

                        # Update conflict status based on resolution result
                        if conflict_id and status:
                            if status == "resolved":
                                new_status = (
                                    ConflictStatus.RESOLVED_AUTO
                                    if resolution_type == "automatic"
                                    else ConflictStatus.RESOLVED_MANUAL
                                )
                                self.update_conflict_status(
                                    conflict_id, new_status.value, detail.get("details")
                                )
                            elif status == "assigned_for_review":
                                self.update_conflict_status(
                                    conflict_id, ConflictStatus.UNDER_REVIEW.value
                                )

        # Store resolution records
        resolutions_to_add = []
        if "resolution_results" in resolution_results:
            for resolution_type, result in resolution_results[
                "resolution_results"
            ].items():
                resolution_record = {
                    "resolution_type": resolution_type,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                resolutions_to_add.append(resolution_record)

        if resolutions_to_add:
            self.add_resolutions(resolutions_to_add, source_step)

        logger.info(f"Stored conflict resolution results from {source_step}")

    def set_text_data(
        self,
        text_data: List[Dict[str, Any]],
        data_type: GraphDataType,
        source_step: str,
    ):
        """Set text data based on type"""
        if data_type == GraphDataType.RAW_TEXT:
            self.raw_text_data = text_data
        elif data_type == GraphDataType.PROCESSED_CHUNKS:
            self.processed_chunks = text_data

        logger.info(f"Set {len(text_data)} {data_type.value} items from {source_step}")

    def set_cleaned_data(self, cleaned_data: List[Dict[str, Any]], source_step: str):
        """Set cleaned data"""
        self.cleaned_data = cleaned_data
        logger.info(f"Set {len(cleaned_data)} cleaned data items from {source_step}")

    def set_validation_results(
        self, validation_results: Dict[str, Any], source_step: str
    ):
        """Set validation results"""
        self.validation_results = validation_results
        logger.info(f"Set validation results from {source_step}")

    def add_step_to_history(self, step_name: str):
        """Track step execution history"""
        if step_name not in self.step_history:
            self.step_history.append(step_name)

    def has_step_completed(self, step_name: str) -> bool:
        """Check if a step has been completed"""
        return step_name in self.step_history

    def get_latest_entities(self) -> List[Dict[str, Any]]:
        """Get latest version của entities"""
        return self.entities

    def get_latest_relationships(self) -> List[Dict[str, Any]]:
        """Get latest version của relationships"""
        return self.relationships

    def get_latest_conflicts(self) -> List[Dict[str, Any]]:
        """Get latest conflicts"""
        return self.conflicts

    def get_latest_resolutions(self) -> List[Dict[str, Any]]:
        """Get latest resolutions"""
        return self.resolutions

    def get_best_text_data(self) -> List[Dict[str, Any]]:
        """Get best available text data, priority: cleaned > chunks > raw"""
        if self.cleaned_data:
            return self.cleaned_data
        elif self.processed_chunks:
            return self.processed_chunks
        else:
            return self.raw_text_data

    def _merge_entity(
        self, existing: Dict[str, Any], new: Dict[str, Any], source_step: str
    ) -> Dict[str, Any]:
        """Merge entity data, keeping provenance"""
        merged = existing.copy()

        # Update with new data
        for key, value in new.items():
            if key.startswith("_"):
                continue  # Skip internal fields

            if value is not None:
                merged[key] = value

        # Add provenance info
        if "_update_history" not in merged:
            merged["_update_history"] = []

        merged["_update_history"].append(
            {
                "step": source_step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_fields": list(new.keys()),
            }
        )

        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "entities": self.entities,
            "relationships": self.relationships,
            "raw_text_data": self.raw_text_data,
            "processed_chunks": self.processed_chunks,
            "cleaned_data": self.cleaned_data,
            "conflicts": self.conflicts,
            "validation_results": self.validation_results,
            "metadata": self.metadata,
            "step_history": self.step_history,
            "summary": {
                "entity_count": len(self.entities),
                "relationship_count": len(self.relationships),
                "text_data_count": len(self.raw_text_data),
                "chunks_count": len(self.processed_chunks),
                "completed_steps": self.step_history,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphState":
        """Create GraphState from dictionary"""
        graph_state = cls()
        if data:
            graph_state.entities = data.get("entities", [])
            graph_state.relationships = data.get("relationships", [])
            graph_state.raw_text_data = data.get("raw_text_data", [])
            graph_state.processed_chunks = data.get("processed_chunks", [])
            graph_state.conflicts = data.get("conflicts", [])
            graph_state.cleaned_data = data.get("cleaned_data", [])
            graph_state.validation_results = data.get("validation_results")
            graph_state.metadata = data.get("metadata", {})
            graph_state.step_history = data.get("step_history", [])
        return graph_state
