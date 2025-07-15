import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class ConflictResolutionExecutor(BaseStepExecutor):
    """Enhanced Conflict Resolution executor với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Conflict resolution cần có conflicts detected hoặc entities"""
        entities = self._get_best_entities()
        has_conflicts = self.graph_state.metadata.get("conflict_detection")
        existing_conflicts = self.graph_state.conflicts

        if not entities and not has_conflicts and not existing_conflicts:
            logger.warning(
                "No entities, detected conflicts, or existing conflicts available for conflict resolution"
            )
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.conflict_resolution import ConflictResolutionTask
            from app.tasks.executors.step_logger import StepLogger

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            # Initialize ConflictResolutionTask
            resolution_task = ConflictResolutionTask(logger=logger)

            # Get configuration
            resolution_types = self.config.get("resolution_types", ["automatic"])
            use_ai = self.config.get("use_ai", True)
            confidence_threshold = self.config.get("confidence_threshold", 0.95)
            batch_size = self.config.get("batch_size", 50)
            severity_filter = self.config.get("severity_filter")
            conflict_type_filter = self.config.get("conflict_type_filter")
            expert_id = self.config.get("expert_id")
            include_context = self.config.get("include_context", True)

            # Lấy conflicts từ graph_state để xử lý
            existing_conflicts = self.graph_state.conflicts
            conflict_ids_from_graph_state = []

            # Extract conflict IDs từ graph state conflicts
            for conflict in existing_conflicts:
                # Chỉ lấy conflicts có status là "detected" hoặc "under_review"
                if conflict.get("status") in ["detected", "under_review"]:
                    if conflict.get("id"):
                        conflict_ids_from_graph_state.append(conflict["id"])
                    elif conflict.get("conflict_id"):
                        conflict_ids_from_graph_state.append(conflict["conflict_id"])

            await self.logger.info(
                f"Found {len(existing_conflicts)} conflicts in graph state for resolution"
            )

            resolution_results = {}
            total_resolved = 0

            await self.logger.info(
                f"Starting conflict resolution with types: {resolution_types}"
            )

            # Automatic resolution
            if "automatic" in resolution_types:
                await self.logger.info("Running automatic conflict resolution")

                # Combine conflict IDs từ config và graph state
                conflicts = self.graph_state.conflicts

                auto_result = await resolution_task.resolve_conflicts_automatically(
                    conflict_ids=conflict_ids_from_graph_state,
                    severity_filter=severity_filter,
                    conflict_type_filter=conflict_type_filter,
                    use_ai=use_ai,
                    confidence_threshold=confidence_threshold,
                    batch_size=batch_size,
                )
                resolution_results["automatic"] = auto_result
                total_resolved += auto_result.get("conflicts_resolved", 0)

                await self.logger.info(
                    f"Automatic resolution completed: {auto_result.get('conflicts_resolved', 0)} resolved"
                )

            # Manual resolution (if expert assignments provided)
            if "manual" in resolution_types and expert_id:
                await self.logger.info(
                    f"Running manual conflict resolution with expert {expert_id}"
                )
                # Get conflicts for review first
                review_result = await resolution_task.get_conflicts_for_review(
                    expert_id=expert_id,
                    severity=severity_filter,
                    conflict_type=conflict_type_filter,
                    include_context=include_context,
                )

                resolution_results["conflicts_for_review"] = review_result

                # If manual resolutions are provided in config
                manual_resolutions = self.config.get("manual_resolutions", [])
                if manual_resolutions:
                    await self.logger.info(
                        f"Applying {len(manual_resolutions)} manual resolutions"
                    )
                    manual_result = await resolution_task.resolve_conflicts_manually(
                        conflict_resolutions=manual_resolutions,
                        expert_id=expert_id,
                    )
                    resolution_results["manual"] = manual_result
                    total_resolved += manual_result.get("conflicts_resolved", 0)

            # Assignment to experts
            if "assign_experts" in resolution_types:
                await self.logger.info("Assigning conflicts to experts")
                conflict_ids = self.config.get("conflict_ids_to_assign", [])

                # Nếu không có specific IDs, sử dụng tất cả conflicts từ graph state
                if not conflict_ids and conflict_ids_from_graph_state:
                    conflict_ids = conflict_ids_from_graph_state

                expert_assignments = self.config.get("expert_assignments", {})
                auto_assign = self.config.get("auto_assign", True)

                if conflict_ids or auto_assign:
                    assign_result = await resolution_task.assign_conflicts_to_experts(
                        conflict_ids=conflict_ids,
                        expert_assignments=expert_assignments,
                        auto_assign=auto_assign,
                    )
                    resolution_results["assignment"] = assign_result

                    await self.logger.info(
                        f"Assignment completed: {assign_result.get('conflicts_assigned', 0)} assigned"
                    )

            # Generate report
            if "generate_report" in resolution_types:
                await self.logger.info("Generating conflict resolution report")
                time_period_days = self.config.get("report_time_period_days", 30)
                include_statistics = self.config.get("include_statistics", True)
                include_trends = self.config.get("include_trends", True)

                report_result = await resolution_task.generate_resolution_report(
                    time_period_days=time_period_days,
                    include_statistics=include_statistics,
                    include_trends=include_trends,
                )
                resolution_results["report"] = report_result

            await self.logger.info(
                f"Conflict resolution completed. Total conflicts resolved: {total_resolved}"
            )

            return {
                "conflict_resolution_result": self._track_provenance(
                    {
                        "resolution_results": resolution_results,
                        "total_conflicts_resolved": total_resolved,
                        "resolution_types": resolution_types,
                        "use_ai": use_ai,
                        "confidence_threshold": confidence_threshold,
                        "processed_conflicts_count": len(existing_conflicts),
                    }
                ),
                "total_resolved": total_resolved,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "conflict_resolution",
                    "resolution_types": resolution_types,
                    "use_ai": use_ai,
                    "confidence_threshold": confidence_threshold,
                    "batch_size": batch_size,
                    "expert_id": expert_id,
                },
            }

        except Exception as e:
            await self.logger.error(f"Conflict resolution execution failed: {str(e)}")
            raise PipelineExecutionError(f"Conflict resolution execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với resolved entities/relationships và resolution results"""
        if "conflict_resolution_result" in step_result:
            resolution_data = step_result["conflict_resolution_result"]
            if "data" in resolution_data:
                data = resolution_data["data"]

                # Store resolution results in metadata
                self.graph_state.metadata["conflict_resolution"] = data

                # Update conflict status và tạo resolution records
                resolution_results = data.get("resolution_results", {})
                all_resolutions = []

                for resolution_type, result in resolution_results.items():
                    if (
                        result.get("status") == "completed"
                        and "resolution_details" in result
                    ):
                        # Process từng resolution detail
                        for detail in result["resolution_details"]:
                            conflict_id = detail.get("conflict_id")
                            status = detail.get("status")

                            # Update conflict status trong graph state
                            if conflict_id and status:
                                if status == "resolved":
                                    new_status = (
                                        "resolved_auto"
                                        if resolution_type == "automatic"
                                        else "resolved_manual"
                                    )
                                    self.graph_state.update_conflict_status(
                                        conflict_id, new_status, detail.get("details")
                                    )
                                elif status == "assigned_for_review":
                                    self.graph_state.update_conflict_status(
                                        conflict_id,
                                        "under_review",
                                        {"reason": detail.get("reason")},
                                    )
                                elif status == "failed" or status == "error":
                                    self.graph_state.update_conflict_status(
                                        conflict_id,
                                        "failed",
                                        {
                                            "error": detail.get(
                                                "error",
                                                detail.get("reason", "Unknown error"),
                                            )
                                        },
                                    )

                            # Tạo resolution record
                            resolution_record = {
                                "conflict_id": conflict_id,
                                "resolution_type": resolution_type,
                                "status": status,
                                "method": detail.get("method"),
                                "details": detail.get("details"),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                            all_resolutions.append(resolution_record)

                    # Tạo summary resolution record cho mỗi type
                    type_summary = {
                        "resolution_type": resolution_type,
                        "status": result.get("status", "completed"),
                        "conflicts_processed": result.get("conflicts_processed", 0),
                        "conflicts_resolved": result.get("conflicts_resolved", 0),
                        "conflicts_failed": result.get("conflicts_failed", 0),
                        "result_summary": result,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    all_resolutions.append(type_summary)

                # Add all resolutions vào graph state
                if all_resolutions:
                    self.graph_state.add_resolutions(all_resolutions, self.step_name)

                # Check if there are updated entities from resolution
                auto_results = resolution_results.get("automatic", {})
                if auto_results and auto_results.get("resolution_details"):
                    resolved_entities = []
                    resolved_relationships = []

                    for detail in auto_results.get("resolution_details", []):
                        if detail.get("status") == "resolved":
                            resolution_detail = detail.get("details", {})

                            # Extract updated entities if any
                            if "updated_entity" in resolution_detail:
                                resolved_entities.append(
                                    resolution_detail["updated_entity"]
                                )

                            # Extract new entities if any
                            if "new_entity" in resolution_detail:
                                resolved_entities.append(
                                    resolution_detail["new_entity"]
                                )

                            # Extract new relationships if any
                            if "new_relationship" in resolution_detail:
                                resolved_relationships.append(
                                    resolution_detail["new_relationship"]
                                )

                    # Update graph state with resolved entities and relationships
                    if resolved_entities:
                        self.graph_state.add_entities(resolved_entities, self.step_name)
                        logger.info(
                            f"Added {len(resolved_entities)} resolved entities to graph state"
                        )

                    if resolved_relationships:
                        self.graph_state.add_relationships(
                            resolved_relationships, self.step_name
                        )
                        logger.info(
                            f"Added {len(resolved_relationships)} resolved relationships to graph state"
                        )

                # Log summary of resolution results
                total_resolved = data.get("total_conflicts_resolved", 0)
                logger.info(
                    f"Added {len(all_resolutions)} resolution records for {total_resolved} processed conflicts to graph state"
                )

                # Log breakdown by resolution type
                for resolution_type, result in resolution_results.items():
                    if resolution_type == "automatic":
                        resolved_count = result.get("conflicts_resolved", 0)
                        assigned_for_review = result.get(
                            "conflicts_assigned_for_review", 0
                        )
                        failed_count = result.get("conflicts_failed", 0)
                        logger.info(
                            f"  - {resolution_type}: {resolved_count} resolved, {assigned_for_review} assigned for review, {failed_count} failed"
                        )
                    elif resolution_type == "manual":
                        resolved_count = result.get("conflicts_resolved", 0)
                        logger.info(f"  - {resolution_type}: {resolved_count} resolved")
                    elif resolution_type == "assignment":
                        assigned_count = result.get("conflicts_assigned", 0)
                        logger.info(
                            f"  - {resolution_type}: {assigned_count} assigned to experts"
                        )
