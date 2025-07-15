from datetime import datetime
from typing import Any, Dict, Optional

from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.assessment import QualityAssessmentService
from app.services.quality.dashboard import QualityDashboardService
from app.services.quality.metrics import QualityMetricsService
from app.services.quality.monitoring import QualityMonitoringService
from app.services.quality.reporting import QualityReportService


class QualityManagementService:
    """Main facade service tổng hợp tất cả quality operations"""

    def __init__(self):
        self.assessment_service = QualityAssessmentService()
        self.report_service = QualityReportService()
        self.monitoring_service = QualityMonitoringService()
        self.metrics_service = QualityMetricsService()
        self.dashboard_service = QualityDashboardService()

        # Legacy dependencies for backward compatibility
        from app.services.conflict_detection import ConflictDetectionService
        from app.services.conflict_resolution import ConflictResolutionService
        from app.services.user import UserService

        self.conflict_detector = ConflictDetectionService()
        self.conflict_resolver = ConflictResolutionService()
        self.user_service = UserService()

    # Quality Assessment - delegate to AssessmentService
    async def assess_quality_dimension(
        self, dimension: QualityDimension, **kwargs
    ) -> float:
        return await self.assessment_service.assess_dimension(dimension, **kwargs)

    async def assess_all_quality_dimensions(
        self, **kwargs
    ) -> Dict[QualityDimension, float]:
        return await self.assessment_service.assess_all_dimensions(**kwargs)

    # Quality Reports - delegate to ReportService
    async def generate_quality_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        return await self.report_service.generate_quality_report(start_date, end_date)

    # Quality Monitoring - delegate to MonitoringService
    async def run_quality_monitoring(self) -> Dict[str, Any]:
        return await self.monitoring_service.run_quality_monitoring()

    # Quality Metrics - delegate to MetricsService
    async def get_trending_metrics(self) -> Dict[str, Any]:
        return await self.metrics_service.get_trending_metrics()

    async def get_conflict_statistics(self) -> Dict[str, Any]:
        return await self.metrics_service.get_conflict_statistics()

    # Dashboard Data - delegate to DashboardService
    async def get_quality_dashboard_data(self) -> Dict[str, Any]:
        return await self.dashboard_service.get_quality_dashboard_data()
