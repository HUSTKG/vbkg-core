from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import ConflictCreate
from app.services.conflict_detection import ConflictDetectionService
from app.tasks.executors import StepLogger


class ConflictDetectionTask:
    """Task for detecting conflicts between entities and relationships"""

    def __init__(self, logger: StepLogger):
        self.logger = logger
        self.conflict_detection_service = ConflictDetectionService()

    async def detect_entity_conflicts(
        self,
        threshold: float = 0.75,
        batch_size: int = 100,
        entity_types: Optional[List[str]] = None,
        entity_ids: Optional[List[str]] = None,
        debug_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Detect conflicts between entities using the conflict detection service.

        Args:
            threshold: Similarity threshold for conflict detection (unused but kept for compatibility)
            batch_size: Number of entities to process in each batch
            entity_types: Types of entities to process, or None to process all types
            entity_ids: Specific entity IDs to check for conflicts
            debug_mode: Enable debug mode for detailed logging

        Returns:
            Dictionary with statistics about the operation
        """
        try:
            # FIXED: Add debug information first
            if debug_mode:
                await self.logger.info(
                    "Running debug check before conflict detection..."
                )
                debug_info = (
                    await self.conflict_detection_service.debug_conflict_detection()
                )
                await self.logger.info(f"Debug info: {debug_info}")

                if debug_info["entities_count"] == 0:
                    await self.logger.warning("No active entities found in database!")
                    return {
                        "status": "completed",
                        "entities_processed": 0,
                        "conflicts_detected": 0,
                        "conflicts_saved": 0,
                        "errors": 0,
                        "debug_info": debug_info,
                        "message": "No active entities found",
                    }

            supabase = await get_supabase()

            await self.logger.info(
                f"Starting conflict detection with batch_size: {batch_size}, "
                f"entity_ids: {len(entity_ids) if entity_ids else 'all'}, "
                f"entity_types: {entity_types}"
            )

            # FIXED: Filter by entity types if specified
            filtered_entity_ids = entity_ids
            if entity_types and not entity_ids:
                # Get entity IDs for specified types
                type_filter_response = (
                    await supabase.table("kg_entities")
                    .select("id")
                    .eq("is_active", True)
                    .in_("entity_type", entity_types)
                    .execute()
                )
                filtered_entity_ids = [e["id"] for e in type_filter_response.data]
                await self.logger.info(
                    f"Filtered to {len(filtered_entity_ids)} entities of types: {entity_types}"
                )

            # Use the conflict detection service
            detected_conflicts = (
                await self.conflict_detection_service.detect_all_conflicts(
                    entity_ids=filtered_entity_ids, batch_size=batch_size
                )
            )

            if not detected_conflicts:
                await self.logger.info("No conflicts detected")
                return {
                    "status": "completed",
                    "entities_processed": 0,
                    "conflicts_detected": 0,
                    "conflicts_saved": 0,
                    "errors": 0,
                    "threshold": threshold,
                    "message": "No conflicts found",
                }

            # Save conflicts to database
            total_conflicts_saved = 0
            total_errors = 0

            await self.logger.info(
                f"Saving {len(detected_conflicts)} detected conflicts to database"
            )

            conflicts = []

            for i, conflict in enumerate(detected_conflicts):
                try:
                    # Convert ConflictCreate to dict for database insertion
                    conflict_data = {
                        "conflict_type": conflict.conflict_type.value,
                        "severity": conflict.severity.value,
                        "description": conflict.description,
                        "confidence_score": conflict.confidence_score,
                        "source_entity_id": conflict.source_entity_id,
                        "target_entity_id": conflict.target_entity_id,
                        "source_relationship_id": conflict.source_relationship_id,
                        "target_relationship_id": conflict.target_relationship_id,
                        "conflicting_attributes": conflict.conflicting_attributes,
                        "context_data": conflict.context_data,
                        "detected_by": conflict.detected_by,
                        "status": "detected",  # Initial status
                        "detected_at": datetime.now().isoformat(),
                    }

                    # Remove None values
                    conflict_data = {
                        k: v for k, v in conflict_data.items() if v is not None
                    }

                    saved_conflict = (
                        await supabase.table("conflicts")
                        .insert(conflict_data)
                        .execute()
                    )
                    total_conflicts_saved += 1

                    conflicts.append(
                        {
                            "id": saved_conflict.data[0].get("id"),
                            **conflict_data,
                        }
                    )

                    # FIXED: Progress logging for large batches
                    if (i + 1) % 10 == 0:
                        await self.logger.info(
                            f"Saved {i + 1}/{len(detected_conflicts)} conflicts"
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error saving conflict {i + 1} to database: {str(e)}"
                    )
                    total_errors += 1

            await self.logger.info(
                f"Conflict detection completed: {len(detected_conflicts)} detected, "
                f"{total_conflicts_saved} saved, {total_errors} errors"
            )

            return {
                "status": "completed",
                "entities_processed": self._estimate_entities_processed(
                    detected_conflicts
                ),
                "conflicts_detected": len(detected_conflicts),
                "conflicts_saved": total_conflicts_saved,
                "conflicts": conflicts,
                "errors": total_errors,
                "threshold": threshold,
                "conflict_types": self._get_conflict_type_summary(detected_conflicts),
                "batch_size": batch_size,
            }

        except Exception as e:
            await self.logger.error(f"Error detecting entity conflicts: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def detect_relationship_conflicts(
        self,
        relationship_ids: Optional[List[str]] = None,
        batch_size: int = 100,
        conflict_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Detect conflicts specifically between relationships.

        Args:
            relationship_ids: Specific relationship IDs to check
            batch_size: Number of relationships to process in each batch
            conflict_types: Types of conflicts to look for

        Returns:
            Dictionary with statistics about the operation
        """
        try:
            await self.logger.info(
                f"Starting relationship conflict detection with batch_size: {batch_size}, "
                f"relationship_ids: {len(relationship_ids) if relationship_ids else 'all'}, "
                f"conflict_types: {conflict_types}"
            )

            # Use the conflict detection service for relationship conflicts
            detected_conflicts = (
                await self.conflict_detection_service.detect_relationship_conflicts(
                    relationship_ids=relationship_ids,
                    batch_size=batch_size,
                    conflict_types=conflict_types,
                )
            )

            if not detected_conflicts:
                await self.logger.info("No relationship conflicts detected")
                return {
                    "status": "completed",
                    "relationships_processed": 0,
                    "conflicts_detected": 0,
                    "conflicts_saved": 0,
                    "errors": 0,
                }

            # Save conflicts to database
            supabase = await get_supabase()
            total_conflicts_saved = 0
            total_errors = 0

            conflicts = []

            for i, conflict in enumerate(detected_conflicts):
                try:
                    conflict_data = {
                        "conflict_type": conflict.conflict_type.value,
                        "severity": conflict.severity.value,
                        "description": conflict.description,
                        "confidence_score": conflict.confidence_score,
                        "source_relationship_id": conflict.source_relationship_id,
                        "target_relationship_id": conflict.target_relationship_id,
                        "conflicting_attributes": conflict.conflicting_attributes,
                        "context_data": conflict.context_data,
                        "detected_by": conflict.detected_by,
                        "status": "detected",
                        "detected_at": datetime.now().isoformat(),
                    }

                    # Remove None values
                    conflict_data = {
                        k: v for k, v in conflict_data.items() if v is not None
                    }

                    saved_conflict = (
                        await supabase.table("conflicts")
                        .insert(conflict_data)
                        .execute()
                    )
                    total_conflicts_saved += 1

                    conflicts.append(
                        {
                            "id": saved_conflict.data[0].get("id"),
                            **conflict_data,
                        }
                    )

                    # Progress logging
                    if (i + 1) % 10 == 0:
                        await self.logger.info(
                            f"Saved {i + 1}/{len(detected_conflicts)} relationship conflicts"
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error saving relationship conflict {i + 1}: {str(e)}"
                    )
                    total_errors += 1

            return {
                "status": "completed",
                "relationships_processed": self._estimate_relationships_processed(
                    detected_conflicts
                ),
                "conflicts_detected": len(detected_conflicts),
                "conflicts_saved": total_conflicts_saved,
                "conflicts": conflicts,
                "errors": total_errors,
                "conflict_types": self._get_conflict_type_summary(detected_conflicts),
            }

        except Exception as e:
            await self.logger.error(f"Error detecting relationship conflicts: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def detect_temporal_conflicts(
        self,
        entity_ids: Optional[List[str]] = None,
        time_window_days: int = 365,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Detect temporal conflicts (timeline inconsistencies, impossible dates).

        Args:
            entity_ids: Specific entity IDs to check
            time_window_days: Time window to check for conflicts
            batch_size: Number of entities to process in each batch

        Returns:
            Dictionary with statistics about the operation
        """
        try:
            await self.logger.info(
                f"Starting temporal conflict detection with {time_window_days} day window, "
                f"entity_ids: {len(entity_ids) if entity_ids else 'all'}"
            )

            detected_conflicts = (
                await self.conflict_detection_service.detect_temporal_conflicts(
                    entity_ids=entity_ids,
                    time_window_days=time_window_days,
                    batch_size=batch_size,
                )
            )

            if not detected_conflicts:
                await self.logger.info("No temporal conflicts detected")
                return {
                    "status": "completed",
                    "entities_processed": 0,
                    "conflicts_detected": 0,
                    "conflicts_saved": 0,
                    "errors": 0,
                }

            # Save conflicts to database
            supabase = await get_supabase()
            total_conflicts_saved = 0
            total_errors = 0

            for i, conflict in enumerate(detected_conflicts):
                try:
                    conflict_data = {
                        "conflict_type": conflict.conflict_type.value,
                        "severity": conflict.severity.value,
                        "description": conflict.description,
                        "confidence_score": conflict.confidence_score,
                        "source_entity_id": conflict.source_entity_id,
                        "target_entity_id": conflict.target_entity_id,
                        "source_relationship_id": conflict.source_relationship_id,
                        "target_relationship_id": conflict.target_relationship_id,
                        "conflicting_attributes": conflict.conflicting_attributes,
                        "context_data": conflict.context_data,
                        "detected_by": conflict.detected_by,
                        "status": "detected",
                        "detected_at": datetime.now().isoformat(),
                    }

                    # Remove None values
                    conflict_data = {
                        k: v for k, v in conflict_data.items() if v is not None
                    }

                    await supabase.table("conflicts").insert(conflict_data).execute()
                    total_conflicts_saved += 1

                    # Progress logging
                    if (i + 1) % 10 == 0:
                        await self.logger.info(
                            f"Saved {i + 1}/{len(detected_conflicts)} temporal conflicts"
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error saving temporal conflict {i + 1}: {str(e)}"
                    )
                    total_errors += 1

            return {
                "status": "completed",
                "entities_processed": self._estimate_entities_processed(
                    detected_conflicts
                ),
                "conflicts_detected": len(detected_conflicts),
                "conflicts_saved": total_conflicts_saved,
                "errors": total_errors,
                "conflict_types": self._get_conflict_type_summary(detected_conflicts),
            }

        except Exception as e:
            await self.logger.error(f"Error detecting temporal conflicts: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def run_comprehensive_conflict_detection(
        self,
        entity_ids: Optional[List[str]] = None,
        batch_size: int = 100,
        include_relationships: bool = True,
        include_temporal: bool = True,
        debug_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Run comprehensive conflict detection across all types.

        Args:
            entity_ids: Specific entity IDs to check
            batch_size: Number of entities to process in each batch
            include_relationships: Whether to check relationship conflicts
            include_temporal: Whether to check temporal conflicts
            debug_mode: Enable debug mode for detailed logging

        Returns:
            Dictionary with comprehensive statistics
        """
        try:
            await self.logger.info("Starting comprehensive conflict detection")

            all_results = {}
            total_conflicts = 0
            total_errors = 0

            # Entity conflicts (always run)
            entity_results = await self.detect_entity_conflicts(
                batch_size=batch_size,
                entity_ids=entity_ids,
                debug_mode=debug_mode,
            )
            all_results["entity_conflicts"] = entity_results
            total_conflicts += entity_results.get("conflicts_detected", 0)
            total_errors += entity_results.get("errors", 0)

            # Relationship conflicts
            if include_relationships:
                relationship_results = await self.detect_relationship_conflicts(
                    batch_size=batch_size,
                )
                all_results["relationship_conflicts"] = relationship_results
                total_conflicts += relationship_results.get("conflicts_detected", 0)
                total_errors += relationship_results.get("errors", 0)

            # Temporal conflicts
            if include_temporal:
                temporal_results = await self.detect_temporal_conflicts(
                    entity_ids=entity_ids,
                    batch_size=batch_size,
                )
                all_results["temporal_conflicts"] = temporal_results
                total_conflicts += temporal_results.get("conflicts_detected", 0)
                total_errors += temporal_results.get("errors", 0)

            await self.logger.info(
                f"Comprehensive conflict detection completed: "
                f"{total_conflicts} total conflicts detected, {total_errors} errors"
            )

            return {
                "status": "completed",
                "total_conflicts_detected": total_conflicts,
                "total_errors": total_errors,
                "detailed_results": all_results,
                "detection_types": {
                    "entities": True,
                    "relationships": include_relationships,
                    "temporal": include_temporal,
                },
            }

        except Exception as e:
            await self.logger.error(
                f"Error in comprehensive conflict detection: {str(e)}"
            )
            return {"status": "failed", "error": str(e)}

    # FIXED: Add debug method for task-level debugging
    async def debug_conflict_detection_setup(self) -> Dict[str, Any]:
        """
        Debug the conflict detection setup and data availability
        """
        try:
            await self.logger.info("Running conflict detection debug setup...")

            debug_info = (
                await self.conflict_detection_service.debug_conflict_detection()
            )

            # Additional task-level debug info
            supabase = await get_supabase()

            # Check table schemas
            try:
                entities_sample = (
                    await supabase.table("kg_entities").select("*").limit(1).execute()
                )
                relationships_sample = (
                    await supabase.table("kg_relationships")
                    .select("*")
                    .limit(1)
                    .execute()
                )
                conflicts_sample = (
                    await supabase.table("conflicts").select("*").limit(1).execute()
                )

                debug_info.update(
                    {
                        "entities_schema": (
                            list(entities_sample.data[0].keys())
                            if entities_sample.data
                            else []
                        ),
                        "relationships_schema": (
                            list(relationships_sample.data[0].keys())
                            if relationships_sample.data
                            else []
                        ),
                        "conflicts_schema": (
                            list(conflicts_sample.data[0].keys())
                            if conflicts_sample.data
                            else []
                        ),
                    }
                )
            except Exception as e:
                await self.logger.warning(f"Could not get schema info: {e}")

            await self.logger.info(f"Debug setup complete: {debug_info}")
            return debug_info

        except Exception as e:
            await self.logger.error(f"Error in debug setup: {str(e)}")
            return {"error": str(e)}

    # Helper methods
    def _estimate_entities_processed(
        self, detected_conflicts: List[ConflictCreate]
    ) -> int:
        """Estimate number of entities processed based on detected conflicts"""
        entity_ids = set()
        for conflict in detected_conflicts:
            if conflict.source_entity_id:
                entity_ids.add(conflict.source_entity_id)
            if conflict.target_entity_id:
                entity_ids.add(conflict.target_entity_id)
        return len(entity_ids)

    def _estimate_relationships_processed(
        self, detected_conflicts: List[ConflictCreate]
    ) -> int:
        """Estimate number of relationships processed based on detected conflicts"""
        relationship_ids = set()
        for conflict in detected_conflicts:
            if conflict.source_relationship_id:
                relationship_ids.add(conflict.source_relationship_id)
            if conflict.target_relationship_id:
                relationship_ids.add(conflict.target_relationship_id)
        return len(relationship_ids)

    def _get_conflict_type_summary(
        self, detected_conflicts: List[ConflictCreate]
    ) -> Dict[str, int]:
        """Get summary of conflict types detected"""
        conflict_types = {}
        for conflict in detected_conflicts:
            conflict_type = conflict.conflict_type.value
            conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
        return conflict_types
