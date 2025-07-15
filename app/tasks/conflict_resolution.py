from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import (ConflictResolution,
                                             ConflictStatus, ConflictType)
from app.services.conflict_resolution import ConflictResolutionService
from app.tasks.executors import StepLogger


class ConflictResolutionTask:
    """Task for resolving conflicts using AI assistance and expert input"""

    def __init__(self, logger: StepLogger):
        self.logger = logger
        self.conflict_resolution_service = ConflictResolutionService()

    async def resolve_conflicts_automatically(
        self,
        conflict_ids: Optional[List[str]] = None,
        severity_filter: Optional[str] = None,
        conflict_type_filter: Optional[ConflictType] = None,
        use_ai: bool = True,
        confidence_threshold: float = 0.95,
        batch_size: int = 50,
        resolve_all_if_no_ids: bool = False,  # FIXED: Add explicit control
    ) -> Dict[str, Any]:
        """
        Attempt to resolve conflicts automatically using AI and rule-based methods.

        Args:
            conflict_ids: Specific conflict IDs to resolve. If None and resolve_all_if_no_ids=False, resolves nothing
            severity_filter: Filter by severity level
            conflict_type_filter: Filter by conflict type
            use_ai: Whether to use AI for resolution suggestions
            confidence_threshold: Minimum confidence for automatic resolution
            batch_size: Number of conflicts to process in each batch
            resolve_all_if_no_ids: If True, resolve all available conflicts when conflict_ids is None

        Returns:
            Dictionary with resolution statistics
        """
        try:
            # FIXED: Validate input and determine what to resolve
            if not conflict_ids and not resolve_all_if_no_ids:
                await self.logger.warning(
                    "No conflict IDs provided and resolve_all_if_no_ids=False. Nothing to resolve."
                )
                return {
                    "status": "completed",
                    "conflicts_processed": 0,
                    "conflicts_resolved": 0,
                    "conflicts_failed": 0,
                    "conflicts_assigned_for_review": 0,
                    "resolution_details": [],
                    "message": "No conflict IDs provided for resolution",
                }

            await self.logger.info(
                f"Starting automatic conflict resolution with confidence threshold: {confidence_threshold}"
            )

            if conflict_ids:
                await self.logger.info(
                    f"Resolving specific conflict IDs: {conflict_ids}"
                )
            else:
                await self.logger.info(
                    "Resolving all available conflicts (resolve_all_if_no_ids=True)"
                )

            # Get conflicts to resolve
            conflicts = await self._get_conflicts_for_resolution(
                conflict_ids=conflict_ids,
                severity_filter=severity_filter,
                conflict_type_filter=conflict_type_filter,
                batch_size=batch_size,
                resolve_all_if_no_ids=resolve_all_if_no_ids,
            )

            if not conflicts:
                await self.logger.info("No conflicts found for automatic resolution")
                return {
                    "status": "completed",
                    "conflicts_processed": 0,
                    "conflicts_resolved": 0,
                    "conflicts_failed": 0,
                    "conflicts_assigned_for_review": 0,
                    "resolution_details": [],
                    "message": "No conflicts found matching criteria",
                }

            await self.logger.info(
                f"Found {len(conflicts)} conflicts for automatic resolution"
            )

            # FIXED: Validate that we're only processing the requested conflicts
            if conflict_ids:
                requested_ids = set(conflict_ids)
                found_ids = {c["id"] for c in conflicts}
                missing_ids = requested_ids - found_ids

                if missing_ids:
                    await self.logger.warning(
                        f"Some requested conflict IDs not found or not resolvable: {missing_ids}"
                    )

                await self.logger.info(
                    f"Processing {len(found_ids)} out of {len(requested_ids)} requested conflicts"
                )

            # Process conflicts
            total_processed = 0
            total_resolved = 0
            total_failed = 0
            total_assigned_for_review = 0
            resolution_details = []

            for conflict in conflicts:
                try:
                    conflict_id = conflict["id"]
                    await self.logger.info(f"Processing conflict {conflict_id}")

                    result = await self.conflict_resolution_service.resolve_conflict_automatically(
                        conflict_id=conflict_id,
                        use_ai=False,
                        confidence_threshold=confidence_threshold,
                    )

                    if result.get("success", False):
                        total_resolved += 1
                        resolution_details.append(
                            {
                                "conflict_id": conflict_id,
                                "status": "resolved",
                                "method": result.get("method"),
                                "details": result.get("details"),
                            }
                        )
                        await self.logger.info(
                            f"Successfully resolved conflict {conflict_id}"
                        )
                    elif result.get("assigned_for_review", False):
                        total_assigned_for_review += 1
                        resolution_details.append(
                            {
                                "conflict_id": conflict_id,
                                "status": "assigned_for_review",
                                "reason": result.get("message"),
                            }
                        )
                        await self.logger.info(
                            f"Assigned conflict {conflict_id} for manual review"
                        )
                    else:
                        total_failed += 1
                        resolution_details.append(
                            {
                                "conflict_id": conflict_id,
                                "status": "failed",
                                "error": result.get("error", "Unknown error"),
                            }
                        )
                        await self.logger.warning(
                            f"Failed to resolve conflict {conflict_id}"
                        )

                    total_processed += 1

                except Exception as e:
                    await self.logger.error(
                        f"Error processing conflict {conflict.get('id', 'unknown')}: {str(e)}"
                    )
                    total_failed += 1
                    total_processed += 1
                    resolution_details.append(
                        {
                            "conflict_id": conflict.get("id", "unknown"),
                            "status": "error",
                            "error": str(e),
                        }
                    )

            await self.logger.info(
                f"Automatic resolution completed: {total_processed} processed, "
                f"{total_resolved} resolved, {total_failed} failed, "
                f"{total_assigned_for_review} assigned for review"
            )

            return {
                "status": "completed",
                "conflicts_processed": total_processed,
                "conflicts_resolved": total_resolved,
                "conflicts_failed": total_failed,
                "conflicts_assigned_for_review": total_assigned_for_review,
                "resolution_details": resolution_details,
                "use_ai": use_ai,
                "confidence_threshold": confidence_threshold,
                "requested_conflict_ids": conflict_ids,  # FIXED: Track what was requested
                "resolve_all_if_no_ids": resolve_all_if_no_ids,
            }

        except Exception as e:
            await self.logger.error(f"Error in automatic conflict resolution: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def resolve_conflicts_manually(
        self,
        conflict_resolutions: List[Dict[str, Any]],
        expert_id: str,
    ) -> Dict[str, Any]:
        """
        Apply manual resolutions by expert.

        Args:
            conflict_resolutions: List of conflict resolution data
                Each item should contain: conflict_id, resolution_method, resolution_data, reasoning
            expert_id: ID of the expert performing the resolution

        Returns:
            Dictionary with resolution statistics
        """
        try:
            await self.logger.info(
                f"Starting manual conflict resolution by expert {expert_id}"
            )

            # FIXED: Extract and validate conflict IDs
            conflict_ids = [r.get("conflict_id") for r in conflict_resolutions]
            valid_conflict_ids = [cid for cid in conflict_ids if cid]

            if len(valid_conflict_ids) != len(conflict_resolutions):
                await self.logger.warning(
                    f"Some resolution entries missing conflict_id"
                )

            await self.logger.info(
                f"Processing {len(valid_conflict_ids)} manual resolutions"
            )

            total_processed = 0
            total_resolved = 0
            total_failed = 0
            resolution_details = []

            for resolution_data in conflict_resolutions:
                try:
                    conflict_id = resolution_data.get("conflict_id")
                    if not conflict_id:
                        await self.logger.error("Resolution data missing conflict_id")
                        total_failed += 1
                        continue

                    # Create ConflictResolution object
                    resolution = ConflictResolution(
                        resolution_method=resolution_data["resolution_method"],
                        resolution_data=resolution_data.get("resolution_data", {}),
                        reasoning=resolution_data.get(
                            "reasoning", "Manual resolution by expert"
                        ),
                        confidence_score=resolution_data.get("confidence_score", 1.0),
                        resolution_timestamp=datetime.now().isoformat(),
                    )

                    await self.logger.info(
                        f"Applying manual resolution for conflict {conflict_id}"
                    )

                    result = await self.conflict_resolution_service.resolve_conflict_manually(
                        conflict_id=conflict_id,
                        resolution=resolution,
                        expert_id=expert_id,
                    )

                    if result.get("success", False):
                        total_resolved += 1
                        resolution_details.append(
                            {
                                "conflict_id": conflict_id,
                                "status": "resolved",
                                "method": result.get("method"),
                                "details": result.get("details"),
                            }
                        )
                        await self.logger.info(
                            f"Successfully resolved conflict {conflict_id} manually"
                        )
                    else:
                        total_failed += 1
                        resolution_details.append(
                            {
                                "conflict_id": conflict_id,
                                "status": "failed",
                                "error": result.get("error", "Unknown error"),
                            }
                        )
                        await self.logger.warning(
                            f"Failed to resolve conflict {conflict_id} manually"
                        )

                    total_processed += 1

                except Exception as e:
                    conflict_id = resolution_data.get("conflict_id", "unknown")
                    await self.logger.error(
                        f"Error in manual resolution of conflict {conflict_id}: {str(e)}"
                    )
                    total_failed += 1
                    total_processed += 1
                    resolution_details.append(
                        {
                            "conflict_id": conflict_id,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            await self.logger.info(
                f"Manual resolution completed: {total_processed} processed, "
                f"{total_resolved} resolved, {total_failed} failed"
            )

            return {
                "status": "completed",
                "conflicts_processed": total_processed,
                "conflicts_resolved": total_resolved,
                "conflicts_failed": total_failed,
                "resolution_details": resolution_details,
                "expert_id": expert_id,
                "requested_conflict_ids": valid_conflict_ids,  # FIXED: Track what was requested
            }

        except Exception as e:
            await self.logger.error(f"Error in manual conflict resolution: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def get_conflicts_for_review(
        self,
        expert_id: Optional[str] = None,
        conflict_ids: Optional[
            List[str]
        ] = None,  # FIXED: Add specific conflict IDs filter
        severity: Optional[str] = None,
        status: Optional[ConflictStatus] = None,
        conflict_type: Optional[ConflictType] = None,
        limit: int = 50,
        include_context: bool = True,
        get_all_if_no_ids: bool = False,  # FIXED: Add explicit control
    ) -> Dict[str, Any]:
        """
        Get conflicts that need expert review.

        Args:
            expert_id: Filter by assigned expert
            conflict_ids: Specific conflict IDs to retrieve. If None and get_all_if_no_ids=False, returns empty
            severity: Filter by severity level
            status: Filter by conflict status
            conflict_type: Filter by conflict type
            limit: Maximum number of conflicts to return
            include_context: Whether to include detailed context
            get_all_if_no_ids: If True, get all available conflicts when conflict_ids is None

        Returns:
            Dictionary with conflicts data
        """
        try:
            # FIXED: Validate input and determine what to retrieve
            if not conflict_ids and not get_all_if_no_ids:
                await self.logger.warning(
                    "No conflict IDs provided and get_all_if_no_ids=False. Returning empty result."
                )
                return {
                    "status": "completed",
                    "conflicts": [],
                    "total_count": 0,
                    "message": "No conflict IDs provided for review",
                    "filters_applied": {
                        "expert_id": expert_id,
                        "conflict_ids": conflict_ids,
                        "severity": severity,
                        "status": status.value if status else None,
                        "conflict_type": conflict_type.value if conflict_type else None,
                        "limit": limit,
                    },
                }

            if conflict_ids:
                await self.logger.info(
                    f"Retrieving specific conflicts for review: {conflict_ids}"
                )
            else:
                await self.logger.info(
                    f"Retrieving all conflicts for review (limit: {limit})"
                )

            # FIXED: Use modified service call that respects conflict_ids
            response = await self._get_specific_conflicts_for_review(
                expert_id=expert_id,
                conflict_ids=conflict_ids,
                severity=severity,
                status=status,
                conflict_type=conflict_type,
                limit=limit,
                get_all_if_no_ids=get_all_if_no_ids,
            )

            conflicts = response.get("data", [])
            total_count = response.get("count", len(conflicts))

            await self.logger.info(f"Retrieved {len(conflicts)} conflicts for review")

            # FIXED: Validate that we're only returning requested conflicts
            if conflict_ids:
                requested_ids = set(conflict_ids)
                found_ids = {c.get("id") for c in conflicts}
                missing_ids = requested_ids - found_ids

                if missing_ids:
                    await self.logger.warning(
                        f"Some requested conflict IDs not found: {missing_ids}"
                    )

            # Add enrichment if requested
            if include_context and conflicts:
                enriched_conflicts = []
                for conflict in conflicts:
                    try:
                        # Get additional context if not already included
                        if not conflict.get("context"):
                            context = await self._get_additional_context(conflict)
                            conflict["context"] = context
                        enriched_conflicts.append(conflict)
                    except Exception as e:
                        await self.logger.warning(
                            f"Error enriching conflict {conflict.get('id')}: {str(e)}"
                        )
                        enriched_conflicts.append(conflict)
                conflicts = enriched_conflicts

            return {
                "status": "completed",
                "conflicts": conflicts,
                "total_count": total_count,
                "filters_applied": {
                    "expert_id": expert_id,
                    "conflict_ids": conflict_ids,
                    "severity": severity,
                    "status": status.value if status else None,
                    "conflict_type": conflict_type.value if conflict_type else None,
                    "limit": limit,
                },
                "include_context": include_context,
                "get_all_if_no_ids": get_all_if_no_ids,
            }

        except Exception as e:
            await self.logger.error(f"Error getting conflicts for review: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def assign_conflicts_to_experts(
        self,
        conflict_ids: List[str],
        expert_assignments: Optional[Dict[str, str]] = None,
        auto_assign: bool = True,
    ) -> Dict[str, Any]:
        """
        Assign conflicts to experts for manual review.

        Args:
            conflict_ids: List of conflict IDs to assign (REQUIRED)
            expert_assignments: Manual assignment mapping {conflict_id: expert_id}
            auto_assign: Whether to auto-assign conflicts to available experts

        Returns:
            Dictionary with assignment statistics
        """
        try:
            # FIXED: Validate required input
            if not conflict_ids:
                await self.logger.warning("No conflict IDs provided for assignment")
                return {
                    "status": "completed",
                    "conflicts_assigned": 0,
                    "conflicts_failed": 0,
                    "assignment_details": [],
                    "message": "No conflict IDs provided for assignment",
                }

            supabase = await get_supabase()

            await self.logger.info(
                f"Assigning {len(conflict_ids)} specific conflicts to experts"
            )

            total_assigned = 0
            total_failed = 0
            assignment_details = []

            for conflict_id in conflict_ids:
                try:
                    expert_id = None

                    # Check manual assignment first
                    if expert_assignments and conflict_id in expert_assignments:
                        expert_id = expert_assignments[conflict_id]
                    elif auto_assign:
                        # Auto-assign to available expert
                        expert_id = await self._get_available_expert()

                    if expert_id:
                        # Update conflict assignment
                        await supabase.table("conflicts").update(
                            {
                                "status": ConflictStatus.UNDER_REVIEW.value,
                                "assigned_to": expert_id,
                                "assigned_at": datetime.now().isoformat(),
                            }
                        ).eq("id", conflict_id).execute()

                        total_assigned += 1
                        assignment_details.append(
                            {
                                "conflict_id": conflict_id,
                                "assigned_to": expert_id,
                                "status": "assigned",
                            }
                        )
                        await self.logger.info(
                            f"Assigned conflict {conflict_id} to expert {expert_id}"
                        )
                    else:
                        total_failed += 1
                        assignment_details.append(
                            {
                                "conflict_id": conflict_id,
                                "status": "failed",
                                "reason": "No available expert",
                            }
                        )
                        await self.logger.warning(
                            f"No expert available for conflict {conflict_id}"
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error assigning conflict {conflict_id}: {str(e)}"
                    )
                    total_failed += 1
                    assignment_details.append(
                        {
                            "conflict_id": conflict_id,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            return {
                "status": "completed",
                "conflicts_assigned": total_assigned,
                "conflicts_failed": total_failed,
                "assignment_details": assignment_details,
                "auto_assign": auto_assign,
                "requested_conflict_ids": conflict_ids,  # FIXED: Track what was requested
            }

        except Exception as e:
            await self.logger.error(f"Error assigning conflicts to experts: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def generate_resolution_report(
        self,
        time_period_days: int = 30,
        include_statistics: bool = True,
        include_trends: bool = True,
        conflict_ids: Optional[
            List[str]
        ] = None,  # FIXED: Add specific conflict IDs filter
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report on conflict resolution activity.

        Args:
            time_period_days: Number of days to include in the report
            include_statistics: Whether to include detailed statistics
            include_trends: Whether to include trend analysis
            conflict_ids: If provided, generate report only for these specific conflicts

        Returns:
            Dictionary with report data
        """
        try:
            from datetime import datetime, timedelta

            supabase = await get_supabase()

            if conflict_ids:
                await self.logger.info(
                    f"Generating conflict resolution report for {len(conflict_ids)} specific conflicts"
                )
            else:
                await self.logger.info(
                    f"Generating conflict resolution report for {time_period_days} days"
                )

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_period_days)

            # FIXED: Get conflicts based on whether specific IDs are provided
            if conflict_ids:
                # Get specific conflicts regardless of time period
                conflicts_list = []
                # Process in chunks to avoid URI too long
                for i in range(0, len(conflict_ids), 50):
                    batch_ids = conflict_ids[i : i + 50]
                    conflicts_response = (
                        await supabase.table("conflicts")
                        .select("*")
                        .in_("id", batch_ids)
                        .execute()
                    )
                    conflicts_list.extend(conflicts_response.data)
                conflicts = conflicts_list
            else:
                # Get conflicts within time period
                conflicts_response = (
                    await supabase.table("conflicts")
                    .select("*")
                    .gte("detected_at", start_date.isoformat())
                    .lte("detected_at", end_date.isoformat())
                    .execute()
                )
                conflicts = conflicts_response.data

            # Basic statistics
            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_period_days,
                },
                "total_conflicts": len(conflicts),
                "specific_conflict_ids": conflict_ids,  # FIXED: Track if this is a specific report
                "status_breakdown": {},
                "type_breakdown": {},
                "severity_breakdown": {},
            }

            # Status breakdown
            for conflict in conflicts:
                status = conflict.get("status", "unknown")
                report["status_breakdown"][status] = (
                    report["status_breakdown"].get(status, 0) + 1
                )

            # Type breakdown
            for conflict in conflicts:
                conflict_type = conflict.get("conflict_type", "unknown")
                report["type_breakdown"][conflict_type] = (
                    report["type_breakdown"].get(conflict_type, 0) + 1
                )

            # Severity breakdown
            for conflict in conflicts:
                severity = conflict.get("severity", "unknown")
                report["severity_breakdown"][severity] = (
                    report["severity_breakdown"].get(severity, 0) + 1
                )

            if include_statistics:
                # Resolution statistics
                resolved_conflicts = [
                    c
                    for c in conflicts
                    if c.get("status") in ["resolved_auto", "resolved_manual"]
                ]
                auto_resolved = [
                    c for c in conflicts if c.get("status") == "resolved_auto"
                ]
                manual_resolved = [
                    c for c in conflicts if c.get("status") == "resolved_manual"
                ]

                report["resolution_statistics"] = {
                    "total_resolved": len(resolved_conflicts),
                    "auto_resolved": len(auto_resolved),
                    "manual_resolved": len(manual_resolved),
                    "resolution_rate": (
                        len(resolved_conflicts) / len(conflicts) if conflicts else 0
                    ),
                    "automation_rate": (
                        len(auto_resolved) / len(resolved_conflicts)
                        if resolved_conflicts
                        else 0
                    ),
                }

                # Expert statistics
                expert_stats = {}
                for conflict in manual_resolved:
                    expert_id = conflict.get("assigned_to")
                    if expert_id:
                        expert_stats[expert_id] = expert_stats.get(expert_id, 0) + 1

                report["expert_statistics"] = expert_stats

            if (
                include_trends and not conflict_ids
            ):  # Only include trends for time-based reports
                # Daily trends
                daily_counts = {}
                for conflict in conflicts:
                    date = conflict.get("detected_at", "").split("T")[0]
                    daily_counts[date] = daily_counts.get(date, 0) + 1

                report["daily_trends"] = daily_counts

            await self.logger.info("Conflict resolution report generated successfully")

            return {
                "status": "completed",
                "report": report,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            await self.logger.error(f"Error generating resolution report: {str(e)}")
            return {"status": "failed", "error": str(e)}

    # Helper methods
    async def _get_conflicts_for_resolution(
        self,
        conflict_ids: Optional[List[str]] = None,
        severity_filter: Optional[str] = None,
        conflict_type_filter: Optional[ConflictType] = None,
        batch_size: int = 50,
        resolve_all_if_no_ids: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get conflicts that are ready for automatic resolution"""
        supabase = await get_supabase()

        if conflict_ids:
            # FIXED: Only get the specific conflicts requested
            await self.logger.info(
                f"Getting {len(conflict_ids)} specific conflicts for resolution"
            )
            conflicts = []
            # Process in chunks to avoid URI too long
            for i in range(0, len(conflict_ids), 50):
                batch_ids = conflict_ids[i : i + 50]
                response = (
                    await supabase.table("conflicts")
                    .select("*")
                    .in_("id", batch_ids)
                    .execute()
                )
                conflicts.extend(response.data)

            # Filter to only resolvable conflicts
            resolvable_conflicts = [
                c for c in conflicts if c.get("status") in ["detected", "under_review"]
            ]

            await self.logger.info(
                f"Found {len(resolvable_conflicts)} resolvable conflicts out of {len(conflicts)} requested"
            )
            return resolvable_conflicts

        elif resolve_all_if_no_ids:
            # Get unresolved conflicts from database
            await self.logger.info("Getting all unresolved conflicts for resolution")
            query = (
                supabase.table("conflicts")
                .select("*")
                .in_("status", ["detected", "under_review"])
            )

            if severity_filter:
                query = query.eq("severity", severity_filter)

            if conflict_type_filter:
                query = query.eq("conflict_type", conflict_type_filter.value)

            query = query.order("detected_at", desc=False).limit(batch_size)

            response = await query.execute()
            return response.data
        else:
            # Return empty list if no IDs provided and not resolving all
            await self.logger.info(
                "No conflict IDs provided and resolve_all_if_no_ids=False, returning empty list"
            )
            return []

    async def _get_specific_conflicts_for_review(
        self,
        expert_id: Optional[str] = None,
        conflict_ids: Optional[List[str]] = None,
        severity: Optional[str] = None,
        status: Optional[ConflictStatus] = None,
        conflict_type: Optional[ConflictType] = None,
        limit: int = 50,
        get_all_if_no_ids: bool = False,
    ) -> Dict[str, Any]:
        """Get specific conflicts for review or all if requested"""

        supabase = await get_supabase()

        if conflict_ids:
            # Get specific conflicts
            conflicts = []
            # Process in chunks to avoid URI too long
            for i in range(0, len(conflict_ids), 50):
                batch_ids = conflict_ids[i : i + 50]
                query = supabase.table("conflicts").select("*").in_("id", batch_ids)

                # Apply additional filters
                if expert_id:
                    query = query.eq("assigned_to", expert_id)
                if severity:
                    query = query.eq("severity", severity)
                if status:
                    query = query.eq("status", status.value)
                if conflict_type:
                    query = query.eq("conflict_type", conflict_type.value)

                response = await query.execute()
                conflicts.extend(response.data)

            return {"data": conflicts, "count": len(conflicts)}

        elif get_all_if_no_ids:
            # Get all conflicts matching filters
            query = supabase.table("conflicts").select("*")

            if expert_id:
                query = query.eq("assigned_to", expert_id)
            if severity:
                query = query.eq("severity", severity)
            if status:
                query = query.eq("status", status.value)
            if conflict_type:
                query = query.eq("conflict_type", conflict_type.value)

            query = query.limit(limit)
            response = await query.execute()
            return {"data": response.data, "count": len(response.data)}
        else:
            # Return empty result
            return {"data": [], "count": 0}

    async def _get_additional_context(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Get additional context for a conflict"""
        # This can be expanded to get more detailed context
        # For now, return basic context
        return {
            "conflict_age_hours": self._calculate_conflict_age(conflict),
            "priority_score": self._calculate_priority_score(conflict),
        }

    def _calculate_conflict_age(self, conflict: Dict[str, Any]) -> float:
        """Calculate how long the conflict has existed (in hours)"""
        try:
            from datetime import datetime

            detected_at = datetime.fromisoformat(
                conflict.get("detected_at", "").replace("Z", "+00:00")
            )
            age = datetime.now() - detected_at.replace(tzinfo=None)
            return age.total_seconds() / 3600  # Convert to hours
        except:
            return 0.0

    def _calculate_priority_score(self, conflict: Dict[str, Any]) -> float:
        """Calculate priority score for conflict resolution"""
        score = 0.0

        # Severity weight
        severity = conflict.get("severity", "low")
        severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        score += severity_weights.get(severity, 0.2)

        # Confidence weight
        confidence = conflict.get("confidence_score", 0.5)
        score += confidence * 0.5

        # Age weight (older conflicts get higher priority)
        age_hours = self._calculate_conflict_age(conflict)
        if age_hours > 24:
            score += 0.3
        elif age_hours > 72:
            score += 0.5

        return min(score, 1.0)

    async def _get_available_expert(self) -> Optional[str]:
        """Get an available expert for conflict assignment"""
        try:
            from app.services.user import UserService

            user_service = UserService()

            # Get experts (simplified - in production you'd consider workload, expertise, etc.)
            experts_response = await user_service.get_users(role_filter="expert")

            if experts_response.data:
                # Simple round-robin assignment (could be more sophisticated)
                return experts_response.data[0]["id"]

            return None
        except Exception as e:
            await self.logger.warning(f"Error getting available expert: {str(e)}")
            return None
