import asyncio
from datetime import datetime
from typing import Any, Dict, List

from app.services.quality.base import BaseQualityService
from app.services.quality.metrics import QualityMetricsService
from app.services.quality.reporting import QualityReportService


class QualityDashboardService(BaseQualityService):
    """Service chuyên cung cấp data cho dashboard"""

    def __init__(self):
        super().__init__()
        self.report_service = QualityReportService()
        self.metrics_service = QualityMetricsService()

    async def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""

        # Get all dashboard data in parallel
        quality_report, conflict_stats, recent_activity, trending_metrics = (
            await asyncio.gather(
                self.report_service.generate_quality_report(),
                self.metrics_service.get_conflict_statistics(),
                self._get_recent_quality_activity(),
                self.metrics_service.get_trending_metrics(),
            )
        )

        return {
            "quality_report": quality_report,
            "conflict_statistics": conflict_stats,
            "recent_activity": recent_activity,
            "trending_metrics": trending_metrics,
            "last_updated": datetime.now().isoformat(),
        }

    async def _get_recent_quality_activity(self) -> List[Dict[str, Any]]:
        """Get recent quality management activity"""
        supabase = await self.get_supabase()

        # Get recent data in parallel
        recent_resolutions, recent_edits = await asyncio.gather(
            self._get_recent_resolutions(supabase), self._get_recent_edits(supabase)
        )

        activity = []

        # Process resolutions
        for resolution in recent_resolutions:
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

        # Process edits
        for edit in recent_edits:
            activity.append(
                {
                    "type": "direct_edit",
                    "timestamp": edit["timestamp"],
                    "description": f"Applied {edit['action']} edit",
                    "user": edit["user_id"],
                }
            )

        # Sort by timestamp and return top 20
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:20]

    async def _get_recent_resolutions(self, supabase):
        """Get recent conflict resolutions"""
        response = (
            await supabase.table("conflicts")
            .select("*")
            .not_.is_("resolution_data", "null")
            .order("updated_at", desc=True)
            .limit(10)
            .execute()
        )
        return response.data

    async def _get_recent_edits(self, supabase):
        """Get recent edit logs"""
        response = (
            await supabase.table("kg_edit_logs")
            .select("*")
            .order("timestamp", desc=True)
            .limit(10)
            .execute()
        )
        return response.data
