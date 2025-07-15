import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from postgrest.types import CountMethod

from app.schemas.conflict_resolution import ConflictStatus, QualityDimension
from app.services.quality.assessment import QualityAssessmentService
from app.services.quality.base import BaseQualityService


class QualityReportService(BaseQualityService):
    """Service chuyên tạo quality reports"""

    def __init__(self):
        super().__init__()
        self.assessment_service = QualityAssessmentService()

    async def generate_quality_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive quality report"""

        # Set default date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get basic statistics and quality scores in parallel
        basic_stats, dimension_scores = await asyncio.gather(
            self._get_basic_statistics(),
            self.assessment_service.assess_all_dimensions(),
        )

        # Calculate overall score
        overall_score = self.assessment_service.calculate_overall_score(
            dimension_scores
        )

        # Generate recommendations
        recommendations = await self._generate_improvement_recommendations(
            dimension_scores
        )

        return {
            "report_date": end_date.isoformat(),
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            **basic_stats,
            "improvement_recommendations": recommendations,
        }

    async def _get_basic_statistics(self) -> Dict[str, Any]:
        """Get basic KG statistics"""
        supabase = await self.get_supabase()

        entities_response, relationships_response, conflicts_response = (
            await asyncio.gather(
                supabase.table("kg_entities")
                .select("*", count=CountMethod.exact)
                .eq("is_active", True)
                .execute(),
                supabase.table("kg_relationships")
                .select("*", count=CountMethod.exact)
                .eq("is_active", True)
                .execute(),
                supabase.table("conflicts")
                .select("*", count=CountMethod.exact)
                .in_(
                    "status",
                    [ConflictStatus.DETECTED.value, ConflictStatus.UNDER_REVIEW.value],
                )
                .execute(),
            )
        )

        return {
            "total_entities": entities_response.count or 0,
            "total_relationships": relationships_response.count or 0,
            "issues_detected": conflicts_response.count or 0,
            "conflicts_pending": conflicts_response.count or 0,
        }

    async def _generate_improvement_recommendations(
        self, dimension_scores: Dict[QualityDimension, float]
    ) -> List[str]:
        """Generate actionable improvement recommendations"""

        recommendations = []
        THRESHOLD = 0.7

        recommendation_map = {
            QualityDimension.COMPLETENESS: [
                "Improve data completeness by requiring more comprehensive entity attributes during extraction",
                "Implement data validation rules to enforce required fields",
            ],
            QualityDimension.ACCURACY: [
                "Increase confidence thresholds for entity extraction",
                "Implement expert verification workflow for low-confidence entities",
                "Use multiple sources for cross-validation",
            ],
            QualityDimension.CONSISTENCY: [
                "Address pending conflicts through expert review",
                "Implement automated conflict resolution for high-confidence cases",
                "Improve source reliability assessment",
            ],
            QualityDimension.VALIDITY: [
                "Strengthen schema validation during data ingestion",
                "Implement data type checking and format validation",
                "Regular schema compliance audits",
            ],
            QualityDimension.UNIQUENESS: [
                "Enhance duplicate detection algorithms",
                "Implement real-time deduplication during entity creation",
                "Regular entity deduplication campaigns",
            ],
        }

        for dimension, score in dimension_scores.items():
            if score < THRESHOLD:
                recommendations.extend(recommendation_map.get(dimension, []))

        return recommendations
