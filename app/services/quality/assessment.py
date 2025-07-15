import asyncio
from typing import Dict

from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.accessors.accuracy import AccuracyAssessor
from app.services.quality.accessors.completeness import CompletenessAssessor
from app.services.quality.accessors.consistency import ConsistencyAssessor
from app.services.quality.accessors.timeliness import TimelinessAssessor
from app.services.quality.accessors.uniqueness import UniquenessAssessor
from app.services.quality.accessors.validity import ValidityAssessor
from app.services.quality.base import BaseQualityService


class QualityAssessmentService(BaseQualityService):
    """Service chuyên đánh giá quality dimensions"""

    def __init__(self):
        super().__init__()
        self.assessors = {
            QualityDimension.COMPLETENESS: CompletenessAssessor(),
            QualityDimension.ACCURACY: AccuracyAssessor(),
            QualityDimension.CONSISTENCY: ConsistencyAssessor(),
            QualityDimension.VALIDITY: ValidityAssessor(),
            QualityDimension.UNIQUENESS: UniquenessAssessor(),
            QualityDimension.TIMELINESS: TimelinessAssessor(),  # Placeholder
        }

    async def assess_all_dimensions(self, **kwargs) -> Dict[QualityDimension, float]:
        """Assess all quality dimensions"""

        # Run assessments in parallel for better performance
        assessment_tasks = [
            self.assess_dimension(dimension, **kwargs) for dimension in QualityDimension
        ]

        results = await asyncio.gather(*assessment_tasks)

        return {list(QualityDimension)[i]: results[i] for i in range(len(results))}

    async def assess_dimension(self, dimension: QualityDimension, **kwargs) -> float:
        """Assess specific quality dimension"""
        assessor = self.assessors.get(dimension)
        if not assessor:
            self.logger.warning(f"No assessor found for dimension {dimension}")
            return 0.0

        try:
            return await assessor.assess(**kwargs)
        except Exception as e:
            self.logger.error(f"Error assessing {dimension}: {e}")
            return 0.0

    def calculate_overall_score(
        self, dimension_scores: Dict[QualityDimension, float]
    ) -> float:
        """Calculate overall quality score from dimension scores"""
        if not dimension_scores:
            return 0.0

        return sum(dimension_scores.values()) / len(dimension_scores)
