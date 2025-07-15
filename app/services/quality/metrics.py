import asyncio
from typing import Any, Dict, List

from postgrest.types import CountMethod

from app.schemas.conflict_resolution import ConflictStatus
from app.services.quality.base import BaseQualityService


class QualityMetricsService(BaseQualityService):
    """Service chuyên tính toán metrics và trends"""

    async def get_trending_metrics(self) -> Dict[str, Any]:
        """Get trending quality metrics over time"""
        supabase = await self.get_supabase()

        # Get last 7 monitoring runs
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

        scores = []
        for run in runs:
            if not run.get("quality_report"):
                scores.append(0.0)
                break
            score = run.get("quality_report", {}).get("overall_score", 0)
            if isinstance(score, str):
                try:
                    score = float(score)
                except ValueError:
                    score = 0.0
            scores.append(score)

        trend = self._calculate_trend(scores)

        return {
            "trend": trend,
            "recent_scores": scores[:7],
            "current_score": scores[0] if scores else 0,
        }

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend direction from scores"""
        if len(scores) < 2:
            return "insufficient_data"

        recent_avg = sum(scores[:3]) / min(3, len(scores))
        older_avg = sum(scores[3:]) / max(1, len(scores) - 3)

        if recent_avg > older_avg + 0.05:
            return "improving"
        elif recent_avg < older_avg - 0.05:
            return "declining"
        else:
            return "stable"

    async def get_conflict_statistics(self) -> Dict[str, Any]:
        """Get conflict statistics for dashboard"""
        supabase = await self.get_supabase()

        # Count conflicts by status and type in parallel
        status_tasks = [
            supabase.table("conflicts")
            .select("*", count=CountMethod.exact)
            .eq("status", status.value)
            .execute()
            for status in ConflictStatus
        ]

        type_tasks = [
            supabase.table("conflicts")
            .select("*", count=CountMethod.exact)
            .eq("conflict_type", type_value)
            .execute()
            for type_value in [
                "duplicate_entity",
                "contradictory_relationship",
                "attribute_mismatch",
            ]
        ]

        status_results, type_results = await asyncio.gather(
            asyncio.gather(*status_tasks), asyncio.gather(*type_tasks)
        )

        # Process results
        status_counts = {
            status.value: result.count or 0
            for status, result in zip(ConflictStatus, status_results)
        }

        type_counts = {
            type_value: result.count or 0
            for type_value, result in zip(
                [
                    "duplicate_entity",
                    "contradictory_relationship",
                    "attribute_mismatch",
                ],
                type_results,
            )
        }

        return {
            "by_status": status_counts,
            "by_type": type_counts,
            "total_pending": status_counts.get("detected", 0)
            + status_counts.get("under_review", 0),
        }
