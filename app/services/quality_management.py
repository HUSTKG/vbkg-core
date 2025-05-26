import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import (ConflictStatus, QualityAssessment,
                                             QualityDimension, QualityReport)
from app.services.conflict_detection import ConflictDetectionService
from app.services.conflict_resolution import ConflictResolutionService
from app.services.user import UserService

logger = logging.getLogger(__name__)


class QualityManagementService:
    """Service for managing overall knowledge graph quality"""

    def __init__(self):
        self.conflict_detector = ConflictDetectionService()
        self.conflict_resolver = ConflictResolutionService()
        self.user_service = UserService()

    async def generate_quality_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> QualityReport:
        """Generate comprehensive quality report"""

        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        supabase = await get_supabase()

        # Get basic statistics
        entities_response = (
            await supabase.table("kg_entities")
            .select("*", count="exact")
            .eq("is_active", True)
            .execute()
        )
        relationships_response = (
            await supabase.table("kg_relationships")
            .select("*", count="exact")
            .eq("is_active", True)
            .execute()
        )
        conflicts_response = (
            await supabase.table("conflicts")
            .select("*", count="exact")
            .in_(
                "status",
                [ConflictStatus.DETECTED.value, ConflictStatus.UNDER_REVIEW.value],
            )
            .execute()
        )

        total_entities = entities_response.count or 0
        total_relationships = relationships_response.count or 0
        conflicts_pending = conflicts_response.count or 0

        # Calculate quality dimensions
        dimension_scores = {}

        # Completeness - percentage of entities with all required attributes
        completeness_score = await self._assess_completeness()
        dimension_scores[QualityDimension.COMPLETENESS] = completeness_score

        # Accuracy - based on confidence scores and verification status
        accuracy_score = await self._assess_accuracy()
        dimension_scores[QualityDimension.ACCURACY] = accuracy_score

        # Consistency - based on conflict detection results
        consistency_score = await self._assess_consistency(
            total_entities, conflicts_pending
        )
        dimension_scores[QualityDimension.CONSISTENCY] = consistency_score

        # Validity - based on schema compliance and data validation
        validity_score = await self._assess_validity()
        dimension_scores[QualityDimension.VALIDITY] = validity_score

        # Uniqueness - based on duplicate detection
        uniqueness_score = await self._assess_uniqueness()
        dimension_scores[QualityDimension.UNIQUENESS] = uniqueness_score

        # Calculate overall score
        overall_score = sum(dimension_scores.values()) / len(dimension_scores)

        # Generate improvement recommendations
        recommendations = await self._generate_improvement_recommendations(
            dimension_scores
        )

        return QualityReport(
            report_date=end_date,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            total_entities=total_entities,
            total_relationships=total_relationships,
            issues_detected=conflicts_pending,
            conflicts_pending=conflicts_pending,
            improvement_recommendations=recommendations,
        )

    async def _assess_completeness(self) -> float:
        """Assess data completeness"""

        supabase = await get_supabase()

        # Get all entities
        entities_response = (
            await supabase.table("kg_entities")
            .select("properties")
            .eq("is_active", True)
            .execute()
        )
        entities = entities_response.data

        if not entities:
            return 1.0

        # Define required attributes per entity type
        required_attributes = {
            "PERSON": ["full_name", "date_of_birth"],
            "ORGANIZATION": ["name", "type"],
            "LOCATION": ["name", "coordinates"],
            # Add more entity types and their required attributes
        }

        complete_entities = 0

        for entity in entities:
            properties = entity.get("properties", {})
            entity_type = entity.get("entity_type", "")

            required_attrs = required_attributes.get(entity_type, [])
            if required_attrs:
                # Check if all required attributes are present and non-empty
                has_all_attrs = all(
                    attr in properties
                    and properties[attr] is not None
                    and str(properties[attr]).strip()
                    for attr in required_attrs
                )
                if has_all_attrs:
                    complete_entities += 1
            else:
                # If no specific requirements, consider complete if has any properties
                if properties:
                    complete_entities += 1

        return complete_entities / len(entities) if entities else 1.0

    async def _assess_accuracy(self) -> float:
        """Assess data accuracy based on confidence and verification"""

        supabase = await get_supabase()

        # Get entities with confidence scores
        entities_response = (
            await supabase.table("kg_entities")
            .select("confidence, is_verified")
            .eq("is_active", True)
            .execute()
        )
        entities = entities_response.data

        if not entities:
            return 1.0

        total_score = 0
        for entity in entities:
            confidence = entity.get("confidence", 0.5)
            is_verified = entity.get("is_verified", False)

            # Boost score for verified entities
            score = confidence
            if is_verified:
                score = min(1.0, score * 1.2)

            total_score += score

        return total_score / len(entities)

    async def _assess_consistency(
        self, total_entities: int, conflicts_pending: int
    ) -> float:
        """Assess data consistency based on conflicts"""

        if total_entities == 0:
            return 1.0

        # Lower consistency score with more conflicts
        conflict_ratio = conflicts_pending / total_entities
        consistency_score = max(
            0.0, 1.0 - (conflict_ratio * 2)
        )  # Penalize conflicts heavily

        return consistency_score

    async def _assess_validity(self) -> float:
        """Assess data validity based on schema compliance"""

        supabase = await get_supabase()

        # Get entities and check for schema violations
        entities_response = (
            await supabase.table("kg_entities")
            .select("entity_type, properties")
            .eq("is_active", True)
            .execute()
        )
        entities = entities_response.data

        if not entities:
            return 1.0

        valid_entities = 0

        # Define schema rules
        entity_schemas = {
            "PERSON": {
                "required_type": str,
                "optional_fields": ["age", "occupation", "nationality"],
            },
            "ORGANIZATION": {
                "required_type": str,
                "optional_fields": ["industry", "founded_year", "headquarters"],
            },
            # Add more schemas
        }

        for entity in entities:
            entity_type = entity.get("entity_type", "")
            properties = entity.get("properties", {})

            schema = entity_schemas.get(entity_type)
            if schema:
                # Basic schema validation
                is_valid = True
                for field, expected_type in schema.items():
                    if field in properties and not isinstance(
                        properties[field], expected_type
                    ):
                        is_valid = False
                        break

                if is_valid:
                    valid_entities += 1
            else:
                # If no schema defined, consider valid
                valid_entities += 1

        return valid_entities / len(entities)

    async def _assess_uniqueness(self) -> float:
        """Assess data uniqueness by detecting duplicates"""

        # Run duplicate detection
        duplicates = await self.conflict_detector.detect_duplicate_entities(
            batch_size=500
        )

        supabase = await get_supabase()
        entities_response = (
            await supabase.table("kg_entities")
            .select("*", count="exact")
            .eq("is_active", True)
            .execute()
        )
        total_entities = entities_response.count or 0

        if total_entities == 0:
            return 1.0

        # Calculate uniqueness score
        duplicate_entities = len(duplicates) * 2  # Each conflict involves 2 entities
        uniqueness_score = max(0.0, 1.0 - (duplicate_entities / total_entities))

        return uniqueness_score

    async def _generate_improvement_recommendations(
        self, dimension_scores: Dict[QualityDimension, float]
    ) -> List[str]:
        """Generate actionable improvement recommendations"""

        recommendations = []

        # Threshold for flagging issues
        THRESHOLD = 0.7

        if dimension_scores.get(QualityDimension.COMPLETENESS, 1.0) < THRESHOLD:
            recommendations.append(
                "Improve data completeness by requiring more comprehensive entity attributes during extraction"
            )
            recommendations.append(
                "Implement data validation rules to enforce required fields"
            )

        if dimension_scores.get(QualityDimension.ACCURACY, 1.0) < THRESHOLD:
            recommendations.append(
                "Increase confidence thresholds for entity extraction"
            )
            recommendations.append(
                "Implement expert verification workflow for low-confidence entities"
            )
            recommendations.append("Use multiple sources for cross-validation")

        if dimension_scores.get(QualityDimension.CONSISTENCY, 1.0) < THRESHOLD:
            recommendations.append("Address pending conflicts through expert review")
            recommendations.append(
                "Implement automated conflict resolution for high-confidence cases"
            )
            recommendations.append("Improve source reliability assessment")

        if dimension_scores.get(QualityDimension.VALIDITY, 1.0) < THRESHOLD:
            recommendations.append("Strengthen schema validation during data ingestion")
            recommendations.append("Implement data type checking and format validation")
            recommendations.append("Regular schema compliance audits")

        if dimension_scores.get(QualityDimension.UNIQUENESS, 1.0) < THRESHOLD:
            recommendations.append("Enhance duplicate detection algorithms")
            recommendations.append(
                "Implement real-time deduplication during entity creation"
            )
            recommendations.append("Regular entity deduplication campaigns")

        return recommendations

    async def run_quality_monitoring(self) -> Dict[str, Any]:
        """Run comprehensive quality monitoring pipeline"""

        logger.info("Starting quality monitoring pipeline")

        results = {"started_at": datetime.now().isoformat(), "steps": []}

        # Step 1: Conflict Detection
        try:
            logger.info("Running conflict detection")
            conflicts = await self.conflict_detector.detect_all_conflicts(
                batch_size=200
            )

            # Save detected conflicts
            supabase = await get_supabase()
            for conflict in conflicts:
                try:
                    await supabase.table("conflicts").insert(
                        conflict.model_dump()
                    ).execute()
                except Exception as e:
                    logger.error(f"Failed to save conflict: {e}")

            results["steps"].append(
                {
                    "step": "conflict_detection",
                    "status": "completed",
                    "conflicts_detected": len(conflicts),
                }
            )

        except Exception as e:
            logger.error(f"Quality conflict detection failed: {e}")
            results["steps"].append(
                {"step": "conflict_detection", "status": "failed", "error": str(e)}
            )

        # Step 2: Auto-resolution
        try:
            logger.info("Running auto-resolution")
            auto_resolved = await self._run_auto_resolution()

            results["steps"].append(
                {
                    "step": "auto_resolution",
                    "status": "completed",
                    "conflicts_resolved": auto_resolved,
                }
            )

        except Exception as e:
            logger.error(f"Auto-resolution failed: {e}")
            results["steps"].append(
                {"step": "auto_resolution", "status": "failed", "error": str(e)}
            )

        # Step 3: Quality Assessment
        try:
            logger.info("Generating quality report")
            quality_report = await self.generate_quality_report()

            results["steps"].append(
                {
                    "step": "quality_assessment",
                    "status": "completed",
                    "overall_score": quality_report.overall_score,
                }
            )

            results["quality_report"] = quality_report.dict()

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            results["steps"].append(
                {"step": "quality_assessment", "status": "failed", "error": str(e)}
            )

        results["completed_at"] = datetime.now().isoformat()

        # Save monitoring results
        try:
            supabase = await get_supabase()
            await supabase.table("quality_monitoring_runs").insert(results).execute()
        except Exception as e:
            logger.error(f"Failed to save monitoring results: {e}")

        return results

    async def _run_auto_resolution(self) -> int:
        """Run automatic conflict resolution"""

        supabase = await get_supabase()

        # Get unresolved conflicts
        conflicts_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("status", ConflictStatus.DETECTED.value)
            .limit(50)
            .execute()
        )

        auto_resolved_count = 0

        for conflict in conflicts_response.data:
            try:
                result = await self.conflict_resolver.resolve_conflict_automatically(
                    UUID(conflict["id"]), use_ai=True, confidence_threshold=0.8
                )

                if result.get("success"):
                    auto_resolved_count += 1

            except Exception as e:
                logger.error(f"Failed to auto-resolve conflict {conflict['id']}: {e}")

        return auto_resolved_count

    async def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """Get data for quality management dashboard"""

        # Get latest quality report
        quality_report = await self.generate_quality_report()

        # Get conflict statistics
        conflict_stats = await self._get_conflict_statistics()

        # Get recent activity
        recent_activity = await self._get_recent_quality_activity()

        # Get trending metrics
        trending_metrics = await self._get_trending_metrics()

        return {
            "quality_report": quality_report.model_dump(),
            "conflict_statistics": conflict_stats,
            "recent_activity": recent_activity,
            "trending_metrics": trending_metrics,
            "last_updated": datetime.now().isoformat(),
        }

    async def _get_conflict_statistics(self) -> Dict[str, Any]:
        """Get conflict statistics for dashboard"""

        supabase = await get_supabase()

        # Count conflicts by status
        status_counts = {}
        for status in ConflictStatus:
            response = (
                await supabase.table("conflicts")
                .select("*", count=CountMethod.exact)
                .eq("status", status.value)
                .execute()
            )
            status_counts[status.value] = response.count or 0

        # Count conflicts by type
        type_counts = {}
        for type_value in [
            "duplicate_entity",
            "contradictory_relationship",
            "attribute_mismatch",
        ]:
            response = (
                await supabase.table("conflicts")
                .select("*", count=CountMethod.exact)
                .eq("conflict_type", type_value)
                .execute()
            )
            type_counts[type_value] = response.count or 0

        return {
            "by_status": status_counts,
            "by_type": type_counts,
            "total_pending": status_counts.get("detected", 0)
            + status_counts.get("under_review", 0),
        }

    async def _get_recent_quality_activity(self) -> List[Dict[str, Any]]:
        """Get recent quality management activity"""

        supabase = await get_supabase()

        # Get recent conflict resolutions
        recent_resolutions = (
            await supabase.table("conflicts")
            .select("*")
            .not_.is_("resolution_data", "null")
            .order("updated_at", desc=True)
            .limit(10)
            .execute()
        )

        # Get recent edit logs
        recent_edits = (
            await supabase.table("kg_edit_logs")
            .select("*")
            .order("timestamp", desc=True)
            .limit(10)
            .execute()
        )

        activity = []

        for resolution in recent_resolutions.data:
            activity.append(
                {
                    "type": "conflict_resolution",
                    "timestamp": resolution.get("updated_at"),
                    "description": f"Resolved {resolution['conflict_type']} conflict",
                    "user": resolution.get("resolution", {}).get(
                        "resolved_by", "system"
                    ),
                }
            )

        for edit in recent_edits.data:
            activity.append(
                {
                    "type": "direct_edit",
                    "timestamp": edit["timestamp"],
                    "description": f"Applied {edit['action']} edit",
                    "user": edit["user_id"],
                }
            )

        # Sort by timestamp
        activity.sort(key=lambda x: x["timestamp"], reverse=True)

        return activity[:20]

    async def _get_trending_metrics(self) -> Dict[str, Any]:
        """Get trending quality metrics over time"""

        # Get quality scores from last 7 monitoring runs
        supabase = await get_supabase()

        response = (
            await supabase.table("quality_monitoring_runs")
            .select("*")
            .order("completed_at", desc=True)
            .limit(7)
            .execute()
        )

        runs = response.data

        if not runs:
            return {"trend": "no_data"}

        # Calculate trends
        scores = [run.get("quality_report", {}).get("overall_score", 0) for run in runs]

        if len(scores) >= 2:
            recent_avg = sum(scores[:3]) / min(3, len(scores))
            older_avg = sum(scores[3:]) / max(1, len(scores) - 3)

            if recent_avg > older_avg + 0.05:
                trend = "improving"
            elif recent_avg < older_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "recent_scores": scores[:7],
            "current_score": scores[0] if scores else 0,
        }
