from datetime import datetime
from typing import Any, Dict

from app.schemas.conflict_resolution import ConflictStatus
from app.services.conflict_detection import ConflictDetectionService
from app.services.quality.base import BaseQualityService
from app.services.quality.reporting import QualityReportService


class QualityMonitoringService(BaseQualityService):
    """Service chuyên monitoring quality pipeline"""

    def __init__(self):
        super().__init__()
        self.report_service = QualityReportService()
        self.conflict_detector = ConflictDetectionService()

    async def run_quality_monitoring(self) -> Dict[str, Any]:
        """Run comprehensive quality monitoring pipeline"""

        from app.core.supabase import get_supabase

        self.logger.info("Starting quality monitoring pipeline")

        results = {"started_at": datetime.now().isoformat(), "steps": []}

        try:
            conflicts = await self.conflict_detector.detect_all_conflicts(
                batch_size=100
            )

            # Lưu conflicts vào database
            supabase = await get_supabase()
            for conflict in conflicts:
                try:
                    await supabase.table("conflicts").insert(
                        conflict.model_dump()
                    ).execute()
                except Exception as e:
                    print(f"Failed to save conflict: {e}")

            # Generate quality report
            quality_report = await self.report_service.generate_quality_report()

            results["steps"].append(
                {
                    "step": "quality_assessment",
                    "status": "completed",
                    "overall_score": quality_report["overall_score"],
                }
            )

            results["quality_report"] = quality_report

            # Run auto-resolution if needed
            if quality_report["conflicts_pending"] > 0:
                auto_resolved = await self._run_auto_resolution()
                results["steps"].append(
                    {
                        "step": "auto_resolution",
                        "status": "completed",
                        "resolved_count": auto_resolved,
                    }
                )

        except Exception as e:
            self.logger.error(f"Quality monitoring failed: {e}")
            results["steps"].append(
                {"step": "quality_assessment", "status": "failed", "error": str(e)}
            )

        results["completed_at"] = datetime.now().isoformat()

        # Save monitoring results
        await self._save_monitoring_results(results)

        return results

    async def _run_auto_resolution(self) -> int:
        """Run automatic conflict resolution"""
        from app.services.conflict_resolution import ConflictResolutionService

        supabase = await self.get_supabase()

        # Get unresolved conflicts
        conflicts_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("status", ConflictStatus.DETECTED.value)
            .limit(50)
            .execute()
        )

        resolver = ConflictResolutionService()
        auto_resolved_count = 0

        for conflict in conflicts_response.data:
            try:
                result = await resolver.resolve_conflict_automatically(
                    conflict["id"], use_ai=True, confidence_threshold=0.8
                )

                if result.get("success"):
                    auto_resolved_count += 1

            except Exception as e:
                self.logger.error(
                    f"Failed to auto-resolve conflict {conflict['id']}: {e}"
                )

        return auto_resolved_count

    async def _save_monitoring_results(self, results: Dict[str, Any]):
        """Save monitoring results to database"""
        try:
            supabase = await self.get_supabase()
            await supabase.table("quality_monitoring_runs").insert(results).execute()
        except Exception as e:
            self.logger.error(f"Failed to save monitoring results: {e}")
