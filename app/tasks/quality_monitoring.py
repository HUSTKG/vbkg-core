import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Quality dimensions for Vietnamese knowledge extraction"""

    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    TIMELINESS = "timeliness"
    TRUSTWORTHINESS = "trustworthiness"
    AVAILABILITY = "availability"


class QualityLevel(str, Enum):
    """Quality assessment levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityMetric:
    """Quality metric definition"""

    dimension: QualityDimension
    name: str
    description: str
    weight: float = 1.0
    threshold_excellent: float = 0.95
    threshold_good: float = 0.85
    threshold_fair: float = 0.70
    threshold_poor: float = 0.50


@dataclass
class QualityAssessment:
    """Quality assessment result"""

    metric: QualityMetric
    score: float
    level: QualityLevel
    details: Dict[str, Any]
    timestamp: datetime
    step_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None


class QualityMonitoringTask:
    """
    Task for quality monitoring and assessment with Vietnamese support
    """

    def __init__(self):
        self.quality_metrics = self._initialize_quality_metrics()

    def _initialize_quality_metrics(self) -> Dict[str, QualityMetric]:
        """Initialize quality metrics for Vietnamese banking knowledge extraction"""
        return {
            # Accuracy metrics
            "entity_extraction_accuracy": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Entity Extraction Accuracy",
                description="Accuracy of Vietnamese entity extraction",
                weight=1.5,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.75,
                threshold_poor=0.60,
            ),
            "relation_extraction_accuracy": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Relation Extraction Accuracy",
                description="Accuracy of Vietnamese relationship extraction",
                weight=1.3,
                threshold_excellent=0.90,
                threshold_good=0.80,
                threshold_fair=0.70,
                threshold_poor=0.55,
            ),
            "entity_resolution_precision": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Entity Resolution Precision",
                description="Precision of Vietnamese entity resolution",
                weight=1.4,
                threshold_excellent=0.95,
                threshold_good=0.88,
                threshold_fair=0.78,
                threshold_poor=0.65,
            ),
            # Consistency metrics
            "ontology_consistency": QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                name="Ontology Consistency",
                description="Consistency with Vietnamese banking ontology",
                weight=1.2,
                threshold_excellent=0.98,
                threshold_good=0.90,
                threshold_fair=0.80,
                threshold_poor=0.70,
            ),
            "vietnamese_text_consistency": QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                name="Vietnamese Text Consistency",
                description="Consistency of Vietnamese text processing",
                weight=1.0,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.75,
                threshold_poor=0.60,
            ),
            # Completeness metrics
            "data_completeness": QualityMetric(
                dimension=QualityDimension.COMPLETENESS,
                name="Data Completeness",
                description="Completeness of Vietnamese data extraction",
                weight=1.1,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.75,
                threshold_poor=0.60,
            ),
            "coverage_completeness": QualityMetric(
                dimension=QualityDimension.COMPLETENESS,
                name="Domain Coverage Completeness",
                description="Coverage of Vietnamese banking domain",
                weight=1.0,
                threshold_excellent=0.90,
                threshold_good=0.80,
                threshold_fair=0.70,
                threshold_poor=0.55,
            ),
            # Vietnamese-specific metrics
            "vietnamese_language_quality": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Vietnamese Language Quality",
                description="Quality of Vietnamese language processing",
                weight=1.2,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.70,
                threshold_poor=0.50,
            ),
        }

    async def monitor_quality(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        step_id: Optional[str] = None,
        pipeline_run_id: Optional[str] = None,
        quality_threshold: float = 0.8,
        generate_recommendations: bool = True,
    ) -> Dict[str, Any]:
        """
        Monitor quality of knowledge extraction with Vietnamese-specific checks

        Args:
            entities: List of extracted entities
            relationships: List of extracted relationships
            step_id: Step ID for tracking
            pipeline_run_id: Pipeline run ID for tracking
            quality_threshold: Minimum quality threshold
            generate_recommendations: Whether to generate improvement recommendations

        Returns:
            Dictionary containing quality assessment results
        """
        try:
            logger.info(
                f"Starting quality monitoring for {len(entities)} entities and {len(relationships)} relationships"
            )

            # Perform quality assessments
            assessments = await self._assess_extraction_quality(
                entities, relationships, step_id, pipeline_run_id
            )

            # Calculate dimension scores
            dimension_scores = self._calculate_dimension_scores(assessments)

            # Calculate overall quality score
            overall_score = self._calculate_overall_score(dimension_scores)
            overall_level = self._score_to_level(overall_score)

            # Generate Vietnamese-specific analysis
            vietnamese_analysis = await self._analyze_vietnamese_specific_quality(
                entities, relationships
            )

            # Generate recommendations if requested
            recommendations = []
            if generate_recommendations:
                recommendations = await self._generate_quality_recommendations(
                    assessments, dimension_scores, vietnamese_analysis
                )

            # Check if quality meets threshold
            passed_threshold = overall_score >= quality_threshold

            result = {
                "overall_score": overall_score,
                "overall_level": overall_level.value,
                "passed_threshold": passed_threshold,
                "dimension_scores": dimension_scores,
                "vietnamese_analysis": vietnamese_analysis,
                "assessments": [self._assessment_to_dict(a) for a in assessments],
                "recommendations": recommendations,
                "quality_threshold": quality_threshold,
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": True,
            }

            # Store quality results
            await self._store_quality_results(result, step_id, pipeline_run_id)

            logger.info(
                f"Quality monitoring completed with overall score: {overall_score:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"Error in quality monitoring: {e}")
            return {
                "overall_score": 0.0,
                "overall_level": QualityLevel.CRITICAL.value,
                "passed_threshold": False,
                "error": str(e),
                "success": False,
            }

    async def _assess_extraction_quality(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        step_id: Optional[str],
        pipeline_run_id: Optional[str],
    ) -> List[QualityAssessment]:
        """Assess quality of extraction results"""
        assessments = []

        # Assess entity extraction quality
        entity_assessment = await self._assess_entity_quality(entities)
        entity_assessment.step_id = step_id
        entity_assessment.pipeline_run_id = pipeline_run_id
        assessments.append(entity_assessment)

        # Assess relationship extraction quality
        relationship_assessment = await self._assess_relationship_quality(relationships)
        relationship_assessment.step_id = step_id
        relationship_assessment.pipeline_run_id = pipeline_run_id
        assessments.append(relationship_assessment)

        # Assess Vietnamese language quality
        vietnamese_assessment = await self._assess_vietnamese_language_quality(
            entities, relationships
        )
        vietnamese_assessment.step_id = step_id
        vietnamese_assessment.pipeline_run_id = pipeline_run_id
        assessments.append(vietnamese_assessment)

        # Assess ontology consistency
        ontology_assessment = await self._assess_ontology_consistency(
            entities, relationships
        )
        ontology_assessment.step_id = step_id
        ontology_assessment.pipeline_run_id = pipeline_run_id
        assessments.append(ontology_assessment)

        # Assess data completeness
        completeness_assessment = await self._assess_data_completeness(
            entities, relationships
        )
        completeness_assessment.step_id = step_id
        completeness_assessment.pipeline_run_id = pipeline_run_id
        assessments.append(completeness_assessment)

        return assessments

    async def _assess_entity_quality(
        self, entities: List[Dict[str, Any]]
    ) -> QualityAssessment:
        """Assess quality of entity extraction"""
        metric = self.quality_metrics["entity_extraction_accuracy"]

        if not entities:
            score = 0.0
        else:
            # Calculate confidence-based accuracy
            confidences = [e.get("confidence", 0.5) for e in entities]
            score = sum(confidences) / len(confidences)

        level = self._determine_quality_level(metric, score)

        details = {
            "total_entities": len(entities),
            "avg_confidence": score,
            "mapped_entities": len([e for e in entities if e.get("is_mapped", False)]),
            "vietnamese_entities": len(
                [e for e in entities if self._is_vietnamese_text(e.get("text", ""))]
            ),
        }

        return QualityAssessment(
            metric=metric,
            score=score,
            level=level,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )

    async def _assess_relationship_quality(
        self, relationships: List[Dict[str, Any]]
    ) -> QualityAssessment:
        """Assess quality of relationship extraction"""
        metric = self.quality_metrics["relation_extraction_accuracy"]

        if not relationships:
            score = 0.0
        else:
            # Calculate confidence-based accuracy
            confidences = [r.get("confidence", 0.5) for r in relationships]
            score = sum(confidences) / len(confidences)

        level = self._determine_quality_level(metric, score)

        details = {
            "total_relationships": len(relationships),
            "avg_confidence": score,
            "mapped_relationships": len(
                [r for r in relationships if r.get("is_mapped", False)]
            ),
            "relationship_types": len(
                set([r.get("relationship_type", "") for r in relationships])
            ),
        }

        return QualityAssessment(
            metric=metric,
            score=score,
            level=level,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )

    async def _assess_vietnamese_language_quality(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> QualityAssessment:
        """Assess Vietnamese language processing quality"""
        metric = self.quality_metrics["vietnamese_language_quality"]

        total_items = len(entities) + len(relationships)
        if total_items == 0:
            score = 0.0
        else:
            vietnamese_score = 0.0

            # Check entity text quality
            for entity in entities:
                entity_text = entity.get("text", entity.get("entity_text", ""))
                vietnamese_score += self._score_vietnamese_text_quality(entity_text)

            # Check relationship text quality
            for rel in relationships:
                source_text = rel.get("source_entity", "")
                target_text = rel.get("target_entity", "")
                vietnamese_score += self._score_vietnamese_text_quality(source_text)
                vietnamese_score += self._score_vietnamese_text_quality(target_text)

            score = vietnamese_score / (
                total_items * 2
            )  # Multiply by 2 for source and target

        level = self._determine_quality_level(metric, score)

        vietnamese_entity_count = len(
            [e for e in entities if self._is_vietnamese_text(e.get("text", ""))]
        )

        details = {
            "vietnamese_entities": vietnamese_entity_count,
            "vietnamese_percentage": (
                (vietnamese_entity_count / len(entities) * 100) if entities else 0
            ),
            "text_quality_issues": self._identify_vietnamese_text_issues(entities),
        }

        return QualityAssessment(
            metric=metric,
            score=score,
            level=level,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )

    async def _assess_ontology_consistency(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> QualityAssessment:
        """Assess ontology consistency"""
        metric = self.quality_metrics["ontology_consistency"]

        total_items = len(entities) + len(relationships)
        if total_items == 0:
            score = 0.0
        else:
            mapped_entities = len([e for e in entities if e.get("ontology_class_id")])
            mapped_relationships = len(
                [r for r in relationships if r.get("ontology_property_id")]
            )

            score = (mapped_entities + mapped_relationships) / total_items

        level = self._determine_quality_level(metric, score)

        details = {
            "total_items": total_items,
            "mapped_entities": mapped_entities,
            "mapped_relationships": mapped_relationships,
            "mapping_percentage": score * 100,
        }

        return QualityAssessment(
            metric=metric,
            score=score,
            level=level,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )

    async def _assess_data_completeness(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> QualityAssessment:
        """Assess data completeness"""
        metric = self.quality_metrics["data_completeness"]

        if not entities and not relationships:
            score = 0.0
        else:
            completeness_scores = []

            # Check entity completeness
            for entity in entities:
                required_fields = ["text", "entity_type", "confidence"]
                present_fields = sum(
                    1 for field in required_fields if entity.get(field)
                )
                completeness_scores.append(present_fields / len(required_fields))

            # Check relationship completeness
            for rel in relationships:
                required_fields = [
                    "source_entity",
                    "target_entity",
                    "relationship_type",
                    "confidence",
                ]
                present_fields = sum(1 for field in required_fields if rel.get(field))
                completeness_scores.append(present_fields / len(required_fields))

            score = (
                sum(completeness_scores) / len(completeness_scores)
                if completeness_scores
                else 0.0
            )

        level = self._determine_quality_level(metric, score)

        details = {
            "total_items": len(entities) + len(relationships),
            "avg_completeness": score,
            "entity_completeness": self._calculate_entity_completeness(entities),
            "relationship_completeness": self._calculate_relationship_completeness(
                relationships
            ),
        }

        return QualityAssessment(
            metric=metric,
            score=score,
            level=level,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )

    def _score_vietnamese_text_quality(self, text: str) -> float:
        """Score Vietnamese text quality"""
        if not text:
            return 0.0

        score = 1.0

        # Check for very short text
        if len(text.strip()) < 2:
            score -= 0.3

        # Check for excessive special characters
        special_char_ratio = len(
            [c for c in text if not c.isalnum() and not c.isspace()]
        ) / len(text)
        if special_char_ratio > 0.3:
            score -= 0.2

        # Check for placeholder text
        placeholder_indicators = ["todo", "tbd", "xxx", "null", "undefined", "test"]
        if any(indicator in text.lower() for indicator in placeholder_indicators):
            score -= 0.5

        # Bonus for proper Vietnamese characters
        if self._is_vietnamese_text(text):
            score += 0.1

        return max(0.0, score)

    def _is_vietnamese_text(self, text: str) -> bool:
        """Check if text contains Vietnamese characters"""
        vietnamese_chars = (
            "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
        )
        return any(char in text.lower() for char in vietnamese_chars)

    def _identify_vietnamese_text_issues(
        self, entities: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify Vietnamese text quality issues"""
        issues = []

        for entity in entities:
            text = entity.get("text", entity.get("entity_text", ""))

            # Check for common Vietnamese text issues
            if len(text.strip()) < 2:
                issues.append(f"Very short text: '{text}'")

            if re.search(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", text):
                issues.append(f"Unusual characters in: '{text}'")

            if any(word in text.lower() for word in ["test", "todo", "xxx"]):
                issues.append(f"Placeholder text: '{text}'")

        return issues[:10]  # Limit to first 10 issues

    def _calculate_entity_completeness(self, entities: List[Dict[str, Any]]) -> float:
        """Calculate entity data completeness"""
        if not entities:
            return 0.0

        required_fields = ["text", "entity_type", "confidence"]
        total_fields = len(entities) * len(required_fields)
        present_fields = 0

        for entity in entities:
            for field in required_fields:
                if entity.get(field):
                    present_fields += 1

        return present_fields / total_fields if total_fields > 0 else 0.0

    def _calculate_relationship_completeness(
        self, relationships: List[Dict[str, Any]]
    ) -> float:
        """Calculate relationship data completeness"""
        if not relationships:
            return 0.0

        required_fields = [
            "source_entity",
            "target_entity",
            "relationship_type",
            "confidence",
        ]
        total_fields = len(relationships) * len(required_fields)
        present_fields = 0

        for rel in relationships:
            for field in required_fields:
                if rel.get(field):
                    present_fields += 1

        return present_fields / total_fields if total_fields > 0 else 0.0

    async def _analyze_vietnamese_specific_quality(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze Vietnamese-specific quality metrics"""
        analysis = {
            "vietnamese_entity_stats": {},
            "banking_domain_coverage": {},
            "language_quality_issues": [],
            "recommendations": [],
        }

        # Analyze Vietnamese entities
        vietnamese_entities = [
            e for e in entities if self._is_vietnamese_text(e.get("text", ""))
        ]
        analysis["vietnamese_entity_stats"] = {
            "total_vietnamese_entities": len(vietnamese_entities),
            "vietnamese_percentage": (
                (len(vietnamese_entities) / len(entities) * 100) if entities else 0
            ),
            "entity_types": self._count_vietnamese_entity_types(vietnamese_entities),
        }

        # Analyze banking domain coverage
        banking_entities = self._identify_banking_entities(entities)
        analysis["banking_domain_coverage"] = {
            "banking_entities": len(banking_entities),
            "banking_percentage": (
                (len(banking_entities) / len(entities) * 100) if entities else 0
            ),
            "banking_categories": self._categorize_banking_entities(banking_entities),
        }

        # Identify language quality issues
        analysis["language_quality_issues"] = self._identify_vietnamese_text_issues(
            entities
        )

        return analysis

    def _count_vietnamese_entity_types(
        self, entities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count Vietnamese entity types"""
        type_counts = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "Unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts

    def _identify_banking_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify banking-related entities"""
        banking_keywords = [
            "ngân hàng",
            "bank",
            "tài khoản",
            "account",
            "giao dịch",
            "transaction",
            "thẻ",
            "card",
            "vay",
            "loan",
            "tiết kiệm",
            "savings",
            "bảo hiểm",
            "insurance",
        ]

        banking_entities = []
        for entity in entities:
            text = entity.get("text", entity.get("entity_text", "")).lower()
            if any(keyword in text for keyword in banking_keywords):
                banking_entities.append(entity)

        return banking_entities

    def _categorize_banking_entities(
        self, entities: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Categorize banking entities by type"""
        categories = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "Unknown")
            categories[entity_type] = categories.get(entity_type, 0) + 1
        return categories

    def _calculate_dimension_scores(
        self, assessments: List[QualityAssessment]
    ) -> Dict[str, Any]:
        """Calculate quality scores by dimension"""
        dimension_scores = {}

        for dimension in QualityDimension:
            dimension_assessments = [
                a for a in assessments if a.metric.dimension == dimension
            ]

            if dimension_assessments:
                # Calculate weighted average
                weighted_sum = sum(
                    a.score * a.metric.weight for a in dimension_assessments
                )
                total_weight = sum(a.metric.weight for a in dimension_assessments)
                avg_score = weighted_sum / total_weight

                dimension_scores[dimension.value] = {
                    "score": avg_score,
                    "level": self._score_to_level(avg_score).value,
                    "assessment_count": len(dimension_assessments),
                }

        return dimension_scores

    def _calculate_overall_score(self, dimension_scores: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        if not dimension_scores:
            return 0.0

        scores = [scores["score"] for scores in dimension_scores.values()]
        return sum(scores) / len(scores)

    def _determine_quality_level(
        self, metric: QualityMetric, score: float
    ) -> QualityLevel:
        """Determine quality level based on score and thresholds"""
        if score >= metric.threshold_excellent:
            return QualityLevel.EXCELLENT
        elif score >= metric.threshold_good:
            return QualityLevel.GOOD
        elif score >= metric.threshold_fair:
            return QualityLevel.FAIR
        elif score >= metric.threshold_poor:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _score_to_level(self, score: float) -> QualityLevel:
        """Convert numeric score to quality level"""
        if score >= 0.95:
            return QualityLevel.EXCELLENT
        elif score >= 0.85:
            return QualityLevel.GOOD
        elif score >= 0.70:
            return QualityLevel.FAIR
        elif score >= 0.50:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    async def _generate_quality_recommendations(
        self,
        assessments: List[QualityAssessment],
        dimension_scores: Dict[str, Any],
        vietnamese_analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate Vietnamese-specific quality improvement recommendations"""
        recommendations = []

        # Check for critical quality issues
        critical_assessments = [
            a for a in assessments if a.level == QualityLevel.CRITICAL
        ]
        for assessment in critical_assessments:
            recommendations.append(
                {
                    "type": "critical",
                    "priority": "high",
                    "metric": assessment.metric.name,
                    "message": f"Critical quality issue in {assessment.metric.name}",
                    "suggestion": f"Review extraction process and data quality for {assessment.metric.dimension.value}",
                    "score": assessment.score,
                }
            )

        # Vietnamese-specific recommendations
        vietnamese_percentage = vietnamese_analysis.get(
            "vietnamese_entity_stats", {}
        ).get("vietnamese_percentage", 0)
        if vietnamese_percentage < 50:
            recommendations.append(
                {
                    "type": "vietnamese_coverage",
                    "priority": "medium",
                    "message": f"Low Vietnamese text coverage ({vietnamese_percentage:.1f}%)",
                    "suggestion": "Consider using Vietnamese-specific NLP models and preprocessing",
                }
            )

        # Banking domain recommendations
        banking_percentage = vietnamese_analysis.get("banking_domain_coverage", {}).get(
            "banking_percentage", 0
        )
        if banking_percentage < 70:
            recommendations.append(
                {
                    "type": "domain_coverage",
                    "priority": "medium",
                    "message": f"Low banking domain coverage ({banking_percentage:.1f}%)",
                    "suggestion": "Expand banking domain ontology and improve domain-specific extraction",
                }
            )

        # Dimension-specific recommendations
        for dimension, scores in dimension_scores.items():
            if scores["score"] < 0.7:
                recommendations.append(
                    {
                        "type": "dimension_improvement",
                        "priority": "medium" if scores["score"] > 0.5 else "high",
                        "dimension": dimension,
                        "message": f"Low {dimension} score ({scores['score']:.2f})",
                        "suggestion": self._get_dimension_suggestion(dimension),
                    }
                )

        return recommendations

    def _get_dimension_suggestion(self, dimension: str) -> str:
        """Get improvement suggestion for specific quality dimension"""
        suggestions = {
            "accuracy": "Improve extraction models, add validation steps, use higher-confidence thresholds",
            "consistency": "Add ontology validation, standardize data formats, implement consistency checks",
            "completeness": "Review data sources, add missing data completion steps, improve field extraction",
            "timeliness": "Implement incremental processing, optimize extraction speed, add real-time updates",
            "trustworthiness": "Add provenance tracking, validate data sources, implement trust scoring",
            "availability": "Improve data accessibility, optimize query performance, add caching",
        }
        return suggestions.get(
            dimension, "Review configuration and add quality improvement steps"
        )

    def _assessment_to_dict(self, assessment: QualityAssessment) -> Dict[str, Any]:
        """Convert QualityAssessment to dictionary"""
        return {
            "metric_name": assessment.metric.name,
            "dimension": assessment.metric.dimension.value,
            "score": assessment.score,
            "level": assessment.level.value,
            "details": assessment.details,
            "timestamp": assessment.timestamp.isoformat(),
            "step_id": assessment.step_id,
            "pipeline_run_id": assessment.pipeline_run_id,
        }

    async def _store_quality_results(
        self,
        quality_result: Dict[str, Any],
        step_id: Optional[str],
        pipeline_run_id: Optional[str],
    ):
        """Store quality monitoring results to database"""
        try:
            supabase = await get_supabase()

            # Store quality report
            report_data = {
                "id": str(uuid4()),
                "step_id": step_id,
                "pipeline_run_id": pipeline_run_id,
                "overall_score": quality_result["overall_score"],
                "overall_level": quality_result["overall_level"],
                "passed_threshold": quality_result["passed_threshold"],
                "dimension_scores": json.dumps(quality_result["dimension_scores"]),
                "vietnamese_analysis": json.dumps(
                    quality_result["vietnamese_analysis"]
                ),
                "recommendations": json.dumps(quality_result["recommendations"]),
                "entity_count": quality_result["entity_count"],
                "relationship_count": quality_result["relationship_count"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            await supabase.from_("pipeline_quality_reports").insert(report_data).execute()

            # Store individual assessments
            for assessment_dict in quality_result["assessments"]:
                assessment_data = {
                    "step_id": step_id,
                    "pipeline_run_id": pipeline_run_id,
                    "metric_name": assessment_dict["metric_name"],
                    "dimension": assessment_dict["dimension"],
                    "score": assessment_dict["score"],
                    "level": assessment_dict["level"],
                    "details": assessment_dict["details"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                await supabase.from_("pipeline_quality_assessments").insert(
                    assessment_data
                ).execute()

        except Exception as e:
            logger.error(f"Error storing quality results: {e}")

    async def get_quality_statistics(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get quality monitoring statistics"""
        try:
            supabase = await get_supabase()

            # Get quality reports
            reports_response = (
                await supabase.from_("pipeline_quality_reports").select("*").execute()
            )
            reports = reports_response.data

            if not reports:
                return {"error": "No quality reports found"}

            # Calculate statistics
            scores = [r["overall_score"] for r in reports]
            levels = [r["overall_level"] for r in reports]

            import statistics

            return {
                "total_reports": len(reports),
                "avg_overall_score": statistics.mean(scores),
                "median_overall_score": statistics.median(scores),
                "score_distribution": {
                    "excellent": len([l for l in levels if l == "excellent"]),
                    "good": len([l for l in levels if l == "good"]),
                    "fair": len([l for l in levels if l == "fair"]),
                    "poor": len([l for l in levels if l == "poor"]),
                    "critical": len([l for l in levels if l == "critical"]),
                },
                "domain": domain,
            }

        except Exception as e:
            logger.error(f"Error getting quality statistics: {e}")
            return {"error": str(e)}
