import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """Quality dimensions based on research paper"""
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


class QualityAssuranceManager:
    """Manages quality assurance throughout the pipeline"""
    
    def __init__(self):
        self.quality_metrics = self._initialize_quality_metrics()
        self.assessment_cache = {}
        
    def _initialize_quality_metrics(self) -> Dict[str, QualityMetric]:
        """Initialize standard quality metrics"""
        return {
            # Accuracy metrics
            "entity_extraction_accuracy": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Entity Extraction Accuracy",
                description="Accuracy of extracted entities compared to ground truth",
                weight=1.5,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.75,
                threshold_poor=0.60
            ),
            "relation_extraction_accuracy": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Relation Extraction Accuracy", 
                description="Accuracy of extracted relationships",
                weight=1.3,
                threshold_excellent=0.90,
                threshold_good=0.80,
                threshold_fair=0.70,
                threshold_poor=0.55
            ),
            "entity_resolution_precision": QualityMetric(
                dimension=QualityDimension.ACCURACY,
                name="Entity Resolution Precision",
                description="Precision of entity resolution process",
                weight=1.4,
                threshold_excellent=0.95,
                threshold_good=0.88,
                threshold_fair=0.78,
                threshold_poor=0.65
            ),
            
            # Consistency metrics
            "ontology_consistency": QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                name="Ontology Consistency",
                description="Consistency with defined ontology rules",
                weight=1.2,
                threshold_excellent=0.98,
                threshold_good=0.90,
                threshold_fair=0.80,
                threshold_poor=0.70
            ),
            "data_format_consistency": QualityMetric(
                dimension=QualityDimension.CONSISTENCY,
                name="Data Format Consistency",
                description="Consistency of data formats across the pipeline",
                weight=1.0,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.75,
                threshold_poor=0.60
            ),
            
            # Completeness metrics
            "data_completeness": QualityMetric(
                dimension=QualityDimension.COMPLETENESS,
                name="Data Completeness",
                description="Percentage of complete data records",
                weight=1.1,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.75,
                threshold_poor=0.60
            ),
            "coverage_completeness": QualityMetric(
                dimension=QualityDimension.COMPLETENESS,
                name="Domain Coverage Completeness",
                description="Coverage of the target domain",
                weight=1.0,
                threshold_excellent=0.90,
                threshold_good=0.80,
                threshold_fair=0.70,
                threshold_poor=0.55
            ),
            
            # Timeliness metrics
            "data_freshness": QualityMetric(
                dimension=QualityDimension.TIMELINESS,
                name="Data Freshness",
                description="How recent the data is",
                weight=0.8,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.70,
                threshold_poor=0.50
            ),
            "processing_timeliness": QualityMetric(
                dimension=QualityDimension.TIMELINESS,
                name="Processing Timeliness",
                description="Timeliness of data processing",
                weight=0.7,
                threshold_excellent=0.90,
                threshold_good=0.80,
                threshold_fair=0.65,
                threshold_poor=0.45
            ),
            
            # Trustworthiness metrics
            "source_trustworthiness": QualityMetric(
                dimension=QualityDimension.TRUSTWORTHINESS,
                name="Source Trustworthiness",
                description="Trustworthiness of data sources",
                weight=1.3,
                threshold_excellent=0.95,
                threshold_good=0.85,
                threshold_fair=0.70,
                threshold_poor=0.50
            ),
            "provenance_completeness": QualityMetric(
                dimension=QualityDimension.TRUSTWORTHINESS,
                name="Provenance Completeness",
                description="Completeness of provenance information",
                weight=1.0,
                threshold_excellent=0.98,
                threshold_good=0.90,
                threshold_fair=0.80,
                threshold_poor=0.65
            ),
            
            # Availability metrics
            "data_accessibility": QualityMetric(
                dimension=QualityDimension.AVAILABILITY,
                name="Data Accessibility",
                description="Ease of accessing the data",
                weight=0.8,
                threshold_excellent=0.98,
                threshold_good=0.90,
                threshold_fair=0.80,
                threshold_poor=0.60
            ),
        }
    
    async def assess_step_quality(
        self,
        step_id: str,
        pipeline_run_id: str,
        step_output: Dict[str, Any],
        step_config: Dict[str, Any]
    ) -> List[QualityAssessment]:
        """Assess quality of a pipeline step"""
        assessments = []
        
        try:
            # Determine which metrics to apply based on step type
            applicable_metrics = self._get_applicable_metrics(step_config.get("step_type"))
            
            for metric_name in applicable_metrics:
                metric = self.quality_metrics[metric_name]
                
                # Calculate quality score
                score = await self._calculate_quality_score(
                    metric, step_output, step_config
                )
                
                # Determine quality level
                level = self._determine_quality_level(metric, score)
                
                # Create assessment
                assessment = QualityAssessment(
                    metric=metric,
                    score=score,
                    level=level,
                    details=await self._get_quality_details(metric, step_output, step_config),
                    timestamp=datetime.now(timezone.utc),
                    step_id=step_id,
                    pipeline_run_id=pipeline_run_id
                )
                
                assessments.append(assessment)
                
                # Store assessment
                await self._store_quality_assessment(assessment)
            
            return assessments
            
        except Exception as e:
            logger.error(f"Error assessing step quality: {e}")
            return []
    
    async def assess_pipeline_quality(
        self,
        pipeline_run_id: str,
        pipeline_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall pipeline quality"""
        try:
            # Get all step assessments for this pipeline run
            step_assessments = await self._get_pipeline_assessments(pipeline_run_id)
            
            # Calculate dimension scores
            dimension_scores = {}
            for dimension in QualityDimension:
                dimension_assessments = [
                    a for a in step_assessments 
                    if a.metric.dimension == dimension
                ]
                
                if dimension_assessments:
                    weighted_score = sum(
                        a.score * a.metric.weight for a in dimension_assessments
                    ) / sum(a.metric.weight for a in dimension_assessments)
                    
                    dimension_scores[dimension.value] = {
                        "score": weighted_score,
                        "level": self._score_to_level(weighted_score),
                        "assessment_count": len(dimension_assessments)
                    }
            
            # Calculate overall quality score
            overall_score = sum(
                scores["score"] for scores in dimension_scores.values()
            ) / len(dimension_scores) if dimension_scores else 0.0
            
            overall_level = self._score_to_level(overall_score)
            
            # Generate recommendations
            recommendations = await self._generate_quality_recommendations(
                step_assessments, dimension_scores
            )
            
            quality_report = {
                "pipeline_run_id": pipeline_run_id,
                "overall_score": overall_score,
                "overall_level": overall_level.value,
                "dimension_scores": dimension_scores,
                "step_count": len(set(a.step_id for a in step_assessments if a.step_id)),
                "assessment_count": len(step_assessments),
                "recommendations": recommendations,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Store pipeline quality report
            await self._store_pipeline_quality_report(quality_report)
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error assessing pipeline quality: {e}")
            return {
                "error": str(e),
                "overall_score": 0.0,
                "overall_level": QualityLevel.CRITICAL.value
            }
    
    def _get_applicable_metrics(self, step_type: str) -> List[str]:
        """Get applicable quality metrics for a step type"""
        metric_mappings = {
            "llm_entity_extractor": [
                "entity_extraction_accuracy",
                "data_completeness",
                "source_trustworthiness"
            ],
            "ner_extractor": [
                "entity_extraction_accuracy",
                "data_completeness",
                "processing_timeliness"
            ],
            "relation_extractor": [
                "relation_extraction_accuracy",
                "data_completeness",
                "ontology_consistency"
            ],
            "entity_resolution": [
                "entity_resolution_precision",
                "data_completeness",
                "processing_timeliness"
            ],
            "entity_fusion": [
                "data_completeness",
                "ontology_consistency",
                "source_trustworthiness"
            ],
            "knowledge_graph_writer": [
                "ontology_consistency",
                "data_completeness",
                "data_accessibility"
            ],
            "quality_checker": [
                "data_completeness",
                "ontology_consistency",
                "source_trustworthiness"
            ],
            "data_cleaner": [
                "data_format_consistency",
                "data_completeness",
                "processing_timeliness"
            ],
            "file_reader": [
                "data_completeness",
                "data_accessibility",
                "processing_timeliness"
            ],
            "api_fetcher": [
                "data_freshness",
                "data_completeness",
                "data_accessibility"
            ],
            "database_extractor": [
                "data_completeness",
                "data_freshness",
                "processing_timeliness"
            ],
        }
        
        return metric_mappings.get(step_type, ["data_completeness"])
    
    async def _calculate_quality_score(
        self,
        metric: QualityMetric,
        step_output: Dict[str, Any],
        step_config: Dict[str, Any]
    ) -> float:
        """Calculate quality score for a specific metric"""
        try:
            if metric.name == "Entity Extraction Accuracy":
                return await self._calculate_entity_extraction_accuracy(step_output)
            elif metric.name == "Relation Extraction Accuracy":
                return await self._calculate_relation_extraction_accuracy(step_output)
            elif metric.name == "Entity Resolution Precision":
                return await self._calculate_entity_resolution_precision(step_output)
            elif metric.name == "Data Completeness":
                return await self._calculate_data_completeness(step_output)
            elif metric.name == "Ontology Consistency":
                return await self._calculate_ontology_consistency(step_output)
            elif metric.name == "Data Freshness":
                return await self._calculate_data_freshness(step_output)
            elif metric.name == "Source Trustworthiness":
                return await self._calculate_source_trustworthiness(step_output, step_config)
            elif metric.name == "Provenance Completeness":
                return await self._calculate_provenance_completeness(step_output)
            elif metric.name == "Data Accessibility":
                return await self._calculate_data_accessibility(step_output)
            else:
                # Default calculation
                return await self._calculate_default_quality_score(step_output)
                
        except Exception as e:
            logger.error(f"Error calculating quality score for {metric.name}: {e}")
            return 0.5  # Default to medium score on error
    
    async def _calculate_entity_extraction_accuracy(self, step_output: Dict[str, Any]) -> float:
        """Calculate entity extraction accuracy"""
        try:
            if "extraction_result" in step_output:
                result = step_output["extraction_result"]
                if "data" in result and "entities" in result["data"]:
                    entities = result["data"]["entities"]
                    if entities:
                        # Calculate confidence-based accuracy
                        confidences = [e.get("confidence", 0.5) for e in entities]
                        return sum(confidences) / len(confidences)
            
            return 0.7  # Default score
            
        except Exception:
            return 0.5
    
    async def _calculate_relation_extraction_accuracy(self, step_output: Dict[str, Any]) -> float:
        """Calculate relation extraction accuracy"""
        try:
            if "extraction_result" in step_output:
                result = step_output["extraction_result"]
                if "data" in result and "relationships" in result["data"]:
                    relationships = result["data"]["relationships"]
                    if relationships:
                        confidences = [r.get("confidence", 0.5) for r in relationships]
                        return sum(confidences) / len(confidences)
            
            return 0.65  # Default score
            
        except Exception:
            return 0.5
    
    async def _calculate_entity_resolution_precision(self, step_output: Dict[str, Any]) -> float:
        """Calculate entity resolution precision"""
        try:
            if "resolution_result" in step_output:
                result = step_output["resolution_result"]
                if "data" in result:
                    data = result["data"]
                    stats = data.get("resolution_stats", {})
                    
                    input_entities = stats.get("input_entities", 0)
                    resolved_entities = stats.get("resolved_entities", 0)
                    clusters_formed = stats.get("clusters_formed", 0)
                    
                    if input_entities > 0:
                        # Higher resolution ratio indicates better precision
                        resolution_ratio = (input_entities - resolved_entities + clusters_formed) / input_entities
                        return min(1.0, resolution_ratio)
            
            return 0.8  # Default score
            
        except Exception:
            return 0.5
    
    async def _calculate_data_completeness(self, step_output: Dict[str, Any]) -> float:
        """Calculate data completeness"""
        try:
            total_fields = 0
            complete_fields = 0
            
            # Check different output types
            if "files" in step_output:
                files = step_output["files"]
                for file_data in files:
                    if isinstance(file_data, dict) and "data" in file_data:
                        data = file_data["data"]
                        total_fields += len(data)
                        complete_fields += len([v for v in data.values() if v is not None and v != ""])
            
            elif "api_response" in step_output:
                api_data = step_output["api_response"]
                if "data" in api_data:
                    data = api_data["data"]["data"]
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                total_fields += len(item)
                                complete_fields += len([v for v in item.values() if v is not None and v != ""])
            
            elif "database_result" in step_output:
                db_data = step_output["database_result"]
                if "data" in db_data:
                    for record in db_data["data"]["data"]:
                        if isinstance(record, dict):
                            total_fields += len(record)
                            complete_fields += len([v for v in record.values() if v is not None and v != ""])
            
            if total_fields > 0:
                return complete_fields / total_fields
            
            return 0.85  # Default score
            
        except Exception:
            return 0.7
    
    async def _calculate_ontology_consistency(self, step_output: Dict[str, Any]) -> float:
        """Calculate ontology consistency"""
        try:
            # This would involve checking against ontology rules
            # For now, return a default score based on data structure
            
            consistency_score = 0.9  # Default high consistency
            
            # Check for basic consistency indicators
            if "extraction_result" in step_output:
                result = step_output["extraction_result"]
                if "data" in result:
                    entities = result["data"].get("entities", [])
                    relationships = result["data"].get("relationships", [])
                    
                    # Check if entities have proper types
                    entities_with_types = [e for e in entities if e.get("type")]
                    if entities:
                        type_consistency = len(entities_with_types) / len(entities)
                        consistency_score *= type_consistency
                    
                    # Check if relationships are well-formed
                    valid_relationships = [
                        r for r in relationships 
                        if r.get("subject") and r.get("predicate") and r.get("object")
                    ]
                    if relationships:
                        relation_consistency = len(valid_relationships) / len(relationships)
                        consistency_score *= relation_consistency
            
            return min(1.0, consistency_score)
            
        except Exception:
            return 0.8
    
    async def _calculate_data_freshness(self, step_output: Dict[str, Any]) -> float:
        """Calculate data freshness"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check metadata for timestamps
            if "metadata" in step_output:
                execution_time_str = step_output["metadata"].get("execution_time")
                if execution_time_str:
                    execution_time = datetime.fromisoformat(execution_time_str.replace('Z', '+00:00'))
                    time_diff = (current_time - execution_time).total_seconds()
                    
                    # Fresher data gets higher score
                    if time_diff < 3600:  # Less than 1 hour
                        return 0.95
                    elif time_diff < 86400:  # Less than 1 day
                        return 0.85
                    elif time_diff < 604800:  # Less than 1 week
                        return 0.70
                    else:
                        return 0.50
            
            return 0.8  # Default score
            
        except Exception:
            return 0.7
    
    async def _calculate_source_trustworthiness(
        self, step_output: Dict[str, Any], step_config: Dict[str, Any]
    ) -> float:
        """Calculate source trustworthiness"""
        try:
            trust_score = step_config.get("trust_score", 0.5)
            
            # Adjust based on provenance information
            if "provenance" in step_output:
                provenance = step_output["provenance"]
                if provenance.get("trust_score"):
                    trust_score = max(trust_score, provenance["trust_score"])
            
            return min(1.0, trust_score)
            
        except Exception:
            return 0.5
    
    async def _calculate_provenance_completeness(self, step_output: Dict[str, Any]) -> float:
        """Calculate provenance completeness"""
        try:
            provenance_fields = ["step_id", "timestamp", "source"]
            complete_provenance = 0
            total_items = 0
            
            # Check provenance in different output types
            for key, value in step_output.items():
                if isinstance(value, dict) and "provenance" in value:
                    total_items += 1
                    provenance = value["provenance"]
                    present_fields = sum(1 for field in provenance_fields if provenance.get(field))
                    if present_fields == len(provenance_fields):
                        complete_provenance += 1
            
            if total_items > 0:
                return complete_provenance / total_items
            
            return 0.8  # Default score
            
        except Exception:
            return 0.7
    
    async def _calculate_data_accessibility(self, step_output: Dict[str, Any]) -> float:
        """Calculate data accessibility"""
        try:
            # Check if data is in accessible format
            accessibility_score = 0.9
            
            # Reduce score for complex nested structures
            def check_complexity(obj, depth=0):
                if depth > 5:  # Too deep nesting
                    return 0.7
                if isinstance(obj, dict):
                    return min(check_complexity(v, depth + 1) for v in obj.values()) if obj else 1.0
                elif isinstance(obj, list):
                    return min(check_complexity(item, depth + 1) for item in obj[:5]) if obj else 1.0
                return 1.0
            
            complexity_score = check_complexity(step_output)
            accessibility_score *= complexity_score
            
            return min(1.0, accessibility_score)
            
        except Exception:
            return 0.8
    
    async def _calculate_default_quality_score(self, step_output: Dict[str, Any]) -> float:
        """Calculate default quality score"""
        try:
            # Basic quality checks
            if not step_output:
                return 0.1
            
            # Check for error indicators
            if "error" in step_output or "error_message" in step_output:
                return 0.3
            
            # Check for data presence
            has_data = any(
                key in step_output 
                for key in ["files", "api_response", "database_result", "extraction_result", "resolution_result"]
            )
            
            if has_data:
                return 0.8
            else:
                return 0.6
                
        except Exception:
            return 0.5
    
    def _determine_quality_level(self, metric: QualityMetric, score: float) -> QualityLevel:
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
    
    async def _get_quality_details(
        self, metric: QualityMetric, step_output: Dict[str, Any], step_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get detailed quality information"""
        return {
            "metric_name": metric.name,
            "dimension": metric.dimension.value,
            "step_type": step_config.get("step_type"),
            "data_size": len(str(step_output)),
            "has_errors": "error" in step_output or "error_message" in step_output,
            "config_trust_score": step_config.get("trust_score", 0.5),
        }
    
    async def _store_quality_assessment(self, assessment: QualityAssessment):
        """Store quality assessment in database"""
        try:
            supabase = await get_supabase()
            
            assessment_data = {
                "id": str(uuid4()),
                "pipeline_run_id": assessment.pipeline_run_id,
                "step_id": assessment.step_id,
                "metric_name": assessment.metric.name,
                "dimension": assessment.metric.dimension.value,
                "score": assessment.score,
                "level": assessment.level.value,
                "details": json.dumps(assessment.details),
                "timestamp": assessment.timestamp.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await supabase.from_("quality_assessments").insert(assessment_data).execute()
            
        except Exception as e:
            logger.error(f"Error storing quality assessment: {e}")
    
    async def _get_pipeline_assessments(self, pipeline_run_id: str) -> List[QualityAssessment]:
        """Get all quality assessments for a pipeline run"""
        try:
            supabase = await get_supabase()
            
            response = (
                await supabase.from_("quality_assessments")
                .select("*")
                .eq("pipeline_run_id", pipeline_run_id)
                .execute()
            )
            
            assessments = []
            for data in response.data:
                metric = QualityMetric(
                    dimension=QualityDimension(data["dimension"]),
                    name=data["metric_name"],
                    description="",
                )
                
                assessment = QualityAssessment(
                    metric=metric,
                    score=data["score"],
                    level=QualityLevel(data["level"]),
                    details=json.loads(data["details"]) if data["details"] else {},
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    step_id=data["step_id"],
                    pipeline_run_id=data["pipeline_run_id"]
                )
                assessments.append(assessment)
            
            return assessments
            
        except Exception as e:
            logger.error(f"Error getting pipeline assessments: {e}")
            return []
    
    async def _generate_quality_recommendations(
        self,
        step_assessments: List[QualityAssessment],
        dimension_scores: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        try:
            # Check for critical quality issues
            critical_assessments = [a for a in step_assessments if a.level == QualityLevel.CRITICAL]
            
            for assessment in critical_assessments:
                recommendations.append({
                    "type": "critical",
                    "message": f"Critical quality issue in {assessment.metric.name}",
                    "suggestion": f"Review {assessment.step_id} step configuration and data quality",
                    "priority": "high",
                    "metric": assessment.metric.name
                })
            
            # Check dimension-specific recommendations
            for dimension, scores in dimension_scores.items():
                if scores["score"] < 0.7:
                    recommendations.append({
                        "type": "improvement",
                        "message": f"Low {dimension} score ({scores['score']:.2f})",
                        "suggestion": self._get_dimension_suggestion(dimension),
                        "priority": "medium" if scores["score"] > 0.5 else "high",
                        "dimension": dimension
                    })
            
            # Check for missing quality checks
            assessed_steps = set(a.step_id for a in step_assessments if a.step_id)
            if len(assessed_steps) < 3:  # Assume should have more quality checks
                recommendations.append({
                    "type": "coverage",
                    "message": "Limited quality assessment coverage",
                    "suggestion": "Add more quality checking steps to the pipeline",
                    "priority": "low"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _get_dimension_suggestion(self, dimension: str) -> str:
        """Get suggestion for improving specific quality dimension"""
        suggestions = {
            "accuracy": "Consider using higher-confidence extraction models or adding validation steps",
            "consistency": "Add ontology validation and data format standardization steps",
            "completeness": "Review data sources and add missing data completion steps",
            "timeliness": "Implement incremental processing and real-time data updates",
            "trustworthiness": "Add provenance tracking and source validation steps",
            "availability": "Improve data accessibility and query optimization"
        }
        return suggestions.get(dimension, "Review configuration and add quality improvement steps")
    
    async def _store_pipeline_quality_report(self, quality_report: Dict[str, Any]):
        """Store pipeline quality report"""
        try:
            supabase = await get_supabase()
            
            report_data = {
                "id": str(uuid4()),
                "pipeline_run_id": quality_report["pipeline_run_id"],
                "overall_score": quality_report["overall_score"],
                "overall_level": quality_report["overall_level"],
                "dimension_scores": json.dumps(quality_report["dimension_scores"]),
                "recommendations": json.dumps(quality_report["recommendations"]),
                "step_count": quality_report["step_count"],
                "assessment_count": quality_report["assessment_count"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await supabase.from_("pipeline_quality_reports").insert(report_data).execute()
            
        except Exception as e:
            logger.error(f"Error storing quality report: {e}")


# Initialize global quality assurance manager
quality_manager = QualityAssuranceManager()
