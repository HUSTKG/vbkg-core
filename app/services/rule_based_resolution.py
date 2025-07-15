import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.conflict_resolution import ResolutionMethod

logger = logging.getLogger(__name__)


@dataclass
class RuleBasedConfig:
    """Configuration for rule-based resolution"""
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.95
    MEDIUM_CONFIDENCE_THRESHOLD = 0.75
    LOW_CONFIDENCE_THRESHOLD = 0.5
    
    # Source reliability thresholds
    HIGH_RELIABILITY_THRESHOLD = 0.8
    RELIABILITY_DIFFERENCE_THRESHOLD = 0.2
    
    # Data completeness thresholds
    COMPLETENESS_DIFFERENCE_THRESHOLD = 0.3
    MIN_COMPLETENESS_SCORE = 0.4
    
    # Temporal thresholds
    RECENT_DATA_DAYS = 30
    OUTDATED_DATA_DAYS = 365
    
    # String similarity thresholds
    HIGH_SIMILARITY_THRESHOLD = 0.9
    MEDIUM_SIMILARITY_THRESHOLD = 0.7
    
    # Pattern matching
    ENTITY_NAME_PATTERNS = [
        r'^\w+\s+\w+$',  # First Last name pattern
        r'^\w+\s+\w+\s+\w+$',  # First Middle Last
        r'^[A-Z]{2,}\s+\w+',  # COMPANY Name pattern
    ]


class RuleBasedResolutionService:
    """Enhanced rule-based conflict resolution service"""
    
    def __init__(self, config: RuleBasedConfig = None):
        self.config = config or RuleBasedConfig()
        self.resolution_stats = {
            'total_resolved': 0,
            'by_method': {},
            'by_confidence': {},
            'failed_resolutions': 0
        }
    
    async def apply_rule_based_resolution(self, conflict: Dict) -> Optional[Dict[str, Any]]:
        """Enhanced rule-based resolution with comprehensive patterns"""
        from app.services.conflict_resolution import ConflictResolutionService

        conflict_resolution_service = ConflictResolutionService()
        
        conflict_type = conflict["conflict_type"]
        confidence = conflict["confidence_score"]
        
        logger.info(f"Applying rule-based resolution for conflict {conflict['id']} of type {conflict_type}")
        
        # Get context data
        context = await conflict_resolution_service._get_conflict_context(conflict)
        
        # Apply type-specific resolution
        resolution = None
        
        if conflict_type == "duplicate_entity":
            resolution = await self._resolve_duplicate_entity(conflict, context)
        elif conflict_type == "contradictory_relationship":
            resolution = await self._resolve_contradictory_relationship(conflict, context)
        elif conflict_type == "attribute_mismatch":
            resolution = await self._resolve_attribute_mismatch(conflict, context)
        elif conflict_type == "temporal_conflict":
            resolution = await self._resolve_temporal_conflict(conflict, context)
        elif conflict_type == "missing_relationship":
            resolution = await self._resolve_missing_relationship(conflict, context)
        elif conflict_type == "source_conflict":
            resolution = await self._resolve_source_conflict(conflict, context)
        elif conflict_type == "schema_mismatch":
            resolution = await self._resolve_schema_mismatch(conflict, context)
        else:
            logger.warning(f"Unknown conflict type: {conflict_type}")
            return None
        
        # Update stats
        if resolution:
            self.resolution_stats['total_resolved'] += 1
            method = resolution['resolution_method']
            self.resolution_stats['by_method'][method] = self.resolution_stats['by_method'].get(method, 0) + 1
            
            conf_level = self._get_confidence_level(resolution.get('confidence', 0))
            self.resolution_stats['by_confidence'][conf_level] = self.resolution_stats['by_confidence'].get(conf_level, 0) + 1
            
            logger.info(f"Rule-based resolution applied: {method} with confidence {resolution.get('confidence', 0):.2f}")
        else:
            self.resolution_stats['failed_resolutions'] += 1
            logger.info(f"No rule-based resolution found for conflict {conflict['id']}")
        
        return resolution
    
    async def _resolve_duplicate_entity(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve duplicate entity conflicts with comprehensive scoring"""
        
        confidence = conflict["confidence_score"]
        source_entity = context.get("source_entity")
        target_entity = context.get("target_entity")
        
        if not source_entity or not target_entity:
            return None
        
        # High confidence duplicates - auto merge
        if confidence >= self.config.HIGH_CONFIDENCE_THRESHOLD:
            return {
                "resolution_method": ResolutionMethod.MERGE_ENTITIES,
                "reasoning": f"High confidence duplicate detection ({confidence:.2f})",
                "confidence": 0.95,
                "actions": {
                    "merge_strategy": "prefer_more_complete",
                    "preserve_all_relationships": True,
                    "confidence_threshold": confidence
                }
            }
        
        # Medium confidence - analyze completeness and quality
        if confidence >= self.config.MEDIUM_CONFIDENCE_THRESHOLD:
            source_score = self._calculate_entity_quality_score(source_entity)
            target_score = self._calculate_entity_quality_score(target_entity)
            
            # Strong quality difference
            if abs(source_score - target_score) > self.config.COMPLETENESS_DIFFERENCE_THRESHOLD:
                if source_score > target_score:
                    return {
                        "resolution_method": ResolutionMethod.KEEP_SOURCE,
                        "reasoning": f"Source entity has higher quality score ({source_score:.2f} vs {target_score:.2f})",
                        "confidence": 0.8,
                        "actions": {
                            "quality_difference": abs(source_score - target_score),
                            "preserve_relationships": True
                        }
                    }
                else:
                    return {
                        "resolution_method": ResolutionMethod.KEEP_TARGET,
                        "reasoning": f"Target entity has higher quality score ({target_score:.2f} vs {source_score:.2f})",
                        "confidence": 0.8,
                        "actions": {
                            "quality_difference": abs(source_score - target_score),
                            "preserve_relationships": True
                        }
                    }
            
            # Similar quality - merge
            return {
                "resolution_method": ResolutionMethod.MERGE_ENTITIES,
                "reasoning": f"Medium confidence with similar quality scores (src: {source_score:.2f}, tgt: {target_score:.2f})",
                "confidence": 0.75,
                "actions": {
                    "merge_strategy": "prefer_more_complete",
                    "preserve_all_relationships": True,
                    "quality_scores": {"source": source_score, "target": target_score}
                }
            }
        
        # Low confidence - check for obvious patterns
        if confidence >= self.config.LOW_CONFIDENCE_THRESHOLD:
            # Name similarity check
            source_name = self._extract_entity_name(source_entity)
            target_name = self._extract_entity_name(target_entity)
            
            if source_name and target_name:
                similarity = self._calculate_string_similarity(source_name, target_name)
                
                if similarity >= self.config.HIGH_SIMILARITY_THRESHOLD:
                    return {
                        "resolution_method": ResolutionMethod.MERGE_ENTITIES,
                        "reasoning": f"High name similarity ({similarity:.2f}): '{source_name}' vs '{target_name}'",
                        "confidence": 0.7,
                        "actions": {
                            "merge_strategy": "prefer_more_complete",
                            "preserve_all_relationships": True,
                            "name_similarity": similarity
                        }
                    }
                
                # Check for abbreviation patterns
                if self._is_abbreviation_match(source_name, target_name):
                    return {
                        "resolution_method": ResolutionMethod.MERGE_ENTITIES,
                        "reasoning": f"Abbreviation match detected: '{source_name}' vs '{target_name}'",
                        "confidence": 0.65,
                        "actions": {
                            "merge_strategy": "prefer_longer_name",
                            "preserve_all_relationships": True,
                            "abbreviation_match": True
                        }
                    }
        
        return None
    
    async def _resolve_contradictory_relationship(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve contradictory relationship conflicts"""
        
        source_rel = context.get("source_relationship")
        target_rel = context.get("target_relationship")
        
        if not source_rel or not target_rel:
            return None
        
        # Temporal analysis
        source_date = self._extract_date_from_relationship(source_rel)
        target_date = self._extract_date_from_relationship(target_rel)
        
        if source_date and target_date:
            # Keep more recent relationship
            if source_date > target_date:
                days_diff = (source_date - target_date).days
                if days_diff > self.config.RECENT_DATA_DAYS:
                    return {
                        "resolution_method": ResolutionMethod.KEEP_SOURCE,
                        "reasoning": f"Source relationship is more recent ({days_diff} days newer)",
                        "confidence": 0.8,
                        "actions": {
                            "temporal_preference": "source",
                            "date_difference_days": days_diff
                        }
                    }
            else:
                days_diff = (target_date - source_date).days
                if days_diff > self.config.RECENT_DATA_DAYS:
                    return {
                        "resolution_method": ResolutionMethod.KEEP_TARGET,
                        "reasoning": f"Target relationship is more recent ({days_diff} days newer)",
                        "confidence": 0.8,
                        "actions": {
                            "temporal_preference": "target",
                            "date_difference_days": days_diff
                        }
                    }
        
        # Source reliability analysis
        source_reliability = self._calculate_source_reliability(source_rel)
        target_reliability = self._calculate_source_reliability(target_rel)
        
        if abs(source_reliability - target_reliability) > self.config.RELIABILITY_DIFFERENCE_THRESHOLD:
            if source_reliability > target_reliability:
                return {
                    "resolution_method": ResolutionMethod.KEEP_SOURCE,
                    "reasoning": f"Source has higher reliability ({source_reliability:.2f} vs {target_reliability:.2f})",
                    "confidence": 0.75,
                    "actions": {
                        "reliability_difference": abs(source_reliability - target_reliability),
                        "chosen_source": "source"
                    }
                }
            else:
                return {
                    "resolution_method": ResolutionMethod.KEEP_TARGET,
                    "reasoning": f"Target has higher reliability ({target_reliability:.2f} vs {source_reliability:.2f})",
                    "confidence": 0.75,
                    "actions": {
                        "reliability_difference": abs(source_reliability - target_reliability),
                        "chosen_source": "target"
                    }
                }
        
        # Check if they can coexist (different time periods)
        if self._can_relationships_coexist(source_rel, target_rel):
            return {
                "resolution_method": ResolutionMethod.KEEP_BOTH,
                "reasoning": "Relationships can coexist in different time periods",
                "confidence": 0.7,
                "actions": {
                    "coexistence_reason": "temporal_separation",
                    "add_temporal_context": True
                }
            }
        
        # Default to deleting conflicting and creating new temporal periods
        return {
            "resolution_method": ResolutionMethod.CREATE_NEW,
            "reasoning": "Creating temporal relationship periods to resolve contradiction",
            "confidence": 0.6,
            "actions": {
                "create_temporal_periods": True,
                "preserve_both_data": True
            }
        }
    
    async def _resolve_attribute_mismatch(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve attribute mismatch conflicts"""
        
        source_entity = context.get("source_entity")
        target_entity = context.get("target_entity")
        
        if not source_entity or not target_entity:
            return None
        
        # Identify conflicting attributes
        source_props = source_entity.get("properties", {})
        target_props = target_entity.get("properties", {})
        
        conflicting_attrs = []
        for key in source_props:
            if key in target_props and source_props[key] != target_props[key]:
                conflicting_attrs.append({
                    "attribute": key,
                    "source_value": source_props[key],
                    "target_value": target_props[key]
                })
        
        if not conflicting_attrs:
            return None
        
        # Analyze each conflicting attribute
        resolutions = []
        
        for attr in conflicting_attrs:
            attr_resolution = self._resolve_single_attribute_conflict(attr, source_entity, target_entity)
            if attr_resolution:
                resolutions.append(attr_resolution)
        
        if not resolutions:
            return None
        
        # Create combined resolution
        return {
            "resolution_method": ResolutionMethod.MANUAL_EDIT,
            "reasoning": f"Resolved {len(resolutions)} attribute conflicts through intelligent merging",
            "confidence": 0.7,
            "actions": {
                "attribute_updates": resolutions,
                "merge_strategy": "intelligent_attribute_merge"
            }
        }
    
    async def _resolve_temporal_conflict(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve temporal conflicts"""
        
        # Extract temporal information
        timeline_data = self._extract_timeline_data(context)
        
        if not timeline_data:
            return None
        
        # Sort events by date
        sorted_events = sorted(timeline_data, key=lambda x: x.get("date", datetime.min))
        
        # Check for logical inconsistencies
        corrections = []
        
        for i, event in enumerate(sorted_events):
            # Check against next event
            if i < len(sorted_events) - 1:
                next_event = sorted_events[i + 1]
                correction = self._check_temporal_logic(event, next_event)
                if correction:
                    corrections.append(correction)
        
        if corrections:
            return {
                "resolution_method": ResolutionMethod.MANUAL_EDIT,
                "reasoning": f"Corrected {len(corrections)} temporal inconsistencies",
                "confidence": 0.75,
                "actions": {
                    "timeline_corrections": corrections,
                    "create_temporal_periods": True
                }
            }
        
        return None
    
    async def _resolve_missing_relationship(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve missing relationship conflicts"""
        
        source_entity = context.get("source_entity")
        target_entity = context.get("target_entity")
        
        if not source_entity or not target_entity:
            return None
        
        # Infer relationship type based on entity types and properties
        relationship_type = self._infer_relationship_type(source_entity, target_entity)
        
        if relationship_type:
            # Calculate confidence based on entity properties
            confidence = self._calculate_relationship_confidence(source_entity, target_entity, relationship_type)
            
            if confidence > self.config.LOW_CONFIDENCE_THRESHOLD:
                return {
                    "resolution_method": ResolutionMethod.CREATE_NEW,
                    "reasoning": f"Inferred {relationship_type} relationship with confidence {confidence:.2f}",
                    "confidence": confidence,
                    "actions": {
                        "create_relationships": [{
                            "source_entity_id": source_entity["id"],
                            "target_entity_id": target_entity["id"],
                            "relationship_type": relationship_type,
                            "confidence": confidence,
                            "inferred": True
                        }]
                    }
                }
        
        return None
    
    async def _resolve_source_conflict(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve source reliability conflicts"""
        
        source_doc = context.get("source_document")
        target_doc = context.get("target_document")
        
        if not source_doc or not target_doc:
            return None
        
        # Calculate source reliability scores
        source_reliability = self._calculate_document_reliability(source_doc)
        target_reliability = self._calculate_document_reliability(target_doc)
        
        if abs(source_reliability - target_reliability) > self.config.RELIABILITY_DIFFERENCE_THRESHOLD:
            if source_reliability > target_reliability:
                return {
                    "resolution_method": ResolutionMethod.KEEP_SOURCE,
                    "reasoning": f"Source document has higher reliability ({source_reliability:.2f} vs {target_reliability:.2f})",
                    "confidence": 0.8,
                    "actions": {
                        "source_priority_reason": "Higher reliability score",
                        "preserve_source_metadata": True
                    }
                }
            else:
                return {
                    "resolution_method": ResolutionMethod.KEEP_TARGET,
                    "reasoning": f"Target document has higher reliability ({target_reliability:.2f} vs {source_reliability:.2f})",
                    "confidence": 0.8,
                    "actions": {
                        "source_priority_reason": "Higher reliability score",
                        "preserve_source_metadata": True
                    }
                }
        
        # Check temporal preference
        source_date = self._extract_document_date(source_doc)
        target_date = self._extract_document_date(target_doc)
        
        if source_date and target_date:
            if source_date > target_date:
                days_diff = (source_date - target_date).days
                if days_diff > self.config.RECENT_DATA_DAYS:
                    return {
                        "resolution_method": ResolutionMethod.KEEP_SOURCE,
                        "reasoning": f"Source document is more recent ({days_diff} days newer)",
                        "confidence": 0.7,
                        "actions": {
                            "temporal_preference": "source",
                            "date_difference_days": days_diff
                        }
                    }
        
        return None
    
    async def _resolve_schema_mismatch(self, conflict: Dict, context: Dict) -> Optional[Dict[str, Any]]:
        """Resolve schema mismatch conflicts"""
        
        source_entity = context.get("source_entity")
        target_entity = context.get("target_entity")
        
        if not source_entity or not target_entity:
            return None
        
        # Analyze schema differences
        schema_transformations = self._analyze_schema_differences(source_entity, target_entity)
        
        if schema_transformations:
            return {
                "resolution_method": ResolutionMethod.MANUAL_EDIT,
                "reasoning": f"Applied {len(schema_transformations)} schema transformations",
                "confidence": 0.8,
                "actions": {
                    "schema_transformations": schema_transformations,
                    "normalization_applied": True
                }
            }
        
        return None
    
    # Helper methods for quality scoring and analysis
    
    def _calculate_entity_quality_score(self, entity: Dict) -> float:
        """Calculate comprehensive quality score for an entity"""
        
        score = 0.0
        
        # Property completeness (0.3 weight)
        props = entity.get("properties", {})
        base_score = min(len(props) * 0.05, 0.3)  # Up to 0.3 for properties
        score += base_score
        
        # Required fields presence (0.2 weight)
        required_fields = ["name", "full_name", "title", "description"]
        present_required = sum(1 for field in required_fields if props.get(field))
        score += (present_required / len(required_fields)) * 0.2
        
        # Confidence score (0.2 weight)
        confidence = entity.get("confidence", 0.0)
        score += confidence * 0.2
        
        # Verification status (0.1 weight)
        if entity.get("is_verified", False):
            score += 0.1
        
        # Source reliability (0.1 weight)
        source_reliability = entity.get("source_reliability", 0.5)
        score += source_reliability * 0.1
        
        # Data freshness (0.1 weight)
        created_at = entity.get("created_at")
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                days_old = (datetime.now() - created_date.replace(tzinfo=None)).days
                freshness_score = max(0, 1 - (days_old / 365))
                score += freshness_score * 0.1
            except:
                pass
        
        return min(score, 1.0)
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using multiple methods"""
        
        # Normalize strings
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Levenshtein distance
        def levenshtein_distance(s1, s2):
            if len(s1) > len(s2):
                s1, s2 = s2, s1
            
            distances = list(range(len(s1) + 1))
            for i2, c2 in enumerate(s2):
                distances_ = [i2+1]
                for i1, c1 in enumerate(s1):
                    if c1 == c2:
                        distances_.append(distances[i1])
                    else:
                        distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
                distances = distances_
            return distances[-1]
        
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
        
        lev_sim = 1 - (levenshtein_distance(str1, str2) / max_len)
        
        # Jaccard similarity (word-based)
        words1 = set(str1.split())
        words2 = set(str2.split())
        intersection = words1 & words2
        union = words1 | words2
        jaccard_sim = len(intersection) / len(union) if union else 0
        
        # Combined similarity
        return (lev_sim * 0.7) + (jaccard_sim * 0.3)
    
    def _is_abbreviation_match(self, name1: str, name2: str) -> bool:
        """Check if one name is an abbreviation of another"""
        
        # Check if one is significantly shorter
        if len(name1) > len(name2) * 2:
            return self._check_abbreviation_pattern(name2, name1)
        elif len(name2) > len(name1) * 2:
            return self._check_abbreviation_pattern(name1, name2)
        
        return False
    
    def _check_abbreviation_pattern(self, short: str, long: str) -> bool:
        """Check if short is an abbreviation of long"""
        
        # Simple acronym check
        long_words = long.split()
        if len(short) == len(long_words):
            acronym = ''.join(word[0].upper() for word in long_words)
            return short.upper() == acronym
        
        # Partial word match
        short_words = short.split()
        long_words = long.split()
        
        if len(short_words) < len(long_words):
            for short_word in short_words:
                if not any(long_word.startswith(short_word) for long_word in long_words):
                    return False
            return True
        
        return False
    
    def _extract_entity_name(self, entity: Dict) -> Optional[str]:
        """Extract the primary name from an entity"""
        
        props = entity.get("properties", {})
        
        # Priority order for name extraction
        name_fields = ["full_name", "name", "title", "entity_text"]
        
        for field in name_fields:
            if field in props and props[field]:
                return str(props[field]).strip()
        
        return entity.get("entity_text", "").strip()
    
    def _calculate_source_reliability(self, relationship: Dict) -> float:
        """Calculate source reliability for a relationship"""
        
        # Base reliability from source document
        source_reliability = relationship.get("source_reliability", 0.5)
        
        # Boost for verified relationships
        if relationship.get("is_verified", False):
            source_reliability += 0.2
        
        # Boost for high confidence
        confidence = relationship.get("confidence", 0.5)
        source_reliability += confidence * 0.1
        
        # Penalize for age
        created_at = relationship.get("created_at")
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                days_old = (datetime.now() - created_date.replace(tzinfo=None)).days
                
                if days_old > self.config.OUTDATED_DATA_DAYS:
                    source_reliability -= 0.1
            except:
                pass
        
        return max(0.0, min(1.0, source_reliability))
    
    def _extract_date_from_relationship(self, relationship: Dict) -> Optional[datetime]:
        """Extract date from relationship properties"""
        
        props = relationship.get("properties", {})
        
        date_fields = ["start_date", "end_date", "date", "created_at", "updated_at"]
        
        for field in date_fields:
            if field in props and props[field]:
                try:
                    return datetime.fromisoformat(str(props[field]).replace("Z", "+00:00"))
                except:
                    continue
        
        # Try relationship-level dates
        try:
            if relationship.get("created_at"):
                return datetime.fromisoformat(relationship["created_at"].replace("Z", "+00:00"))
        except:
            pass
        
        return None
    
    def _can_relationships_coexist(self, rel1: Dict, rel2: Dict) -> bool:
        """Check if two relationships can coexist in different time periods"""
        
        date1 = self._extract_date_from_relationship(rel1)
        date2 = self._extract_date_from_relationship(rel2)
        
        if not date1 or not date2:
            return False
        
        # If they're more than 30 days apart, they can likely coexist
        return abs((date1 - date2).days) > 30
    
    def _resolve_single_attribute_conflict(self, attr: Dict, source_entity: Dict, target_entity: Dict) -> Optional[Dict]:
        """Resolve a single attribute conflict"""
        
        attr_name = attr["attribute"]
        source_value = attr["source_value"]
        target_value = attr["target_value"]
        
        # String values - choose longer if significant difference
        if isinstance(source_value, str) and isinstance(target_value, str):
            if len(target_value) > len(source_value) * 1.5:
                return {
                    "entity_id": target_entity["id"],
                    "attribute_name": attr_name,
                    "new_value": target_value,
                    "update_reason": "Target value is significantly more complete"
                }
            elif len(source_value) > len(target_value) * 1.5:
                return {
                    "entity_id": source_entity["id"],
                    "attribute_name": attr_name,
                    "new_value": source_value,
                    "update_reason": "Source value is significantly more complete"
                }
        
        # Number values - choose higher confidence source
        source_confidence = source_entity.get("confidence", 0.5)
        target_confidence = target_entity.get("confidence", 0.5)
        
        if source_confidence > target_confidence:
            return {
                "entity_id": source_entity["id"],
                "attribute_name": attr_name,
                "new_value": source_value,
                "update_reason": f"Source has higher confidence ({source_confidence:.2f} vs {target_confidence:.2f})"
            }
        elif target_confidence > source_confidence:
            return {
                "entity_id": target_entity["id"],
                "attribute_name": attr_name,
                "new_value": target_value,
                "update_reason": f"Target has higher confidence ({target_confidence:.2f} vs {source_confidence:.2f})"
            }
        
        return None
    
    def _extract_timeline_data(self, context: Dict) -> List[Dict]:
        """Extract timeline data from context"""
        
        timeline = []
        
        # Extract from entities
        for entity_key in ["source_entity", "target_entity"]:
            entity = context.get(entity_key)
            if entity:
                props = entity.get("properties", {})
                for key, value in props.items():
                    if "date" in key.lower():
                        try:
                            date_obj = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                            timeline.append({
                                "entity_id": entity["id"],
                                "event_type": key,
                                "date": date_obj,
                                "value": value
                            })
                        except:
                            continue
        
        return timeline
    
    def _check_temporal_logic(self, event1: Dict, event2: Dict) -> Optional[Dict]:
        """Check temporal logic between two events"""
        
        # Example: start_date should be before end_date
        if event1["event_type"] == "start_date" and event2["event_type"] == "end_date":
            if event1["date"] > event2["date"]:
                return {
                    "event_id": event1["entity_id"],
                    "corrected_date": event2["date"] - timedelta(days=1),
                    "confidence": 0.8,
                    "source_priority": "logical_correction"
                }
        
        return None
    
    def _infer_relationship_type(self, source_entity: Dict, target_entity: Dict) -> Optional[str]:
        """Infer relationship type based on entity types and properties"""
        
        source_type = source_entity.get("entity_type", "")
        target_type = target_entity.get("entity_type", "")
        
        # Common relationship patterns
        if source_type == "PERSON" and target_type == "ORGANIZATION":
            return "works_at"
        elif source_type == "ORGANIZATION" and target_type == "PERSON":
            return "employs"
        elif source_type == "PERSON" and target_type == "PERSON":
            return "knows"
        elif source_type == "ORGANIZATION" and target_type == "ORGANIZATION":
            return "partner_with"
        
        return None
    
    def _calculate_relationship_confidence(self, source_entity: Dict, target_entity: Dict, relationship_type: str) -> float:
        """Calculate confidence for inferred relationship"""
        
        base_confidence = 0.5
        
        # Boost for high entity confidences
        source_conf = source_entity.get("confidence", 0.5)
        target_conf = target_entity.get("confidence", 0.5)
        avg_conf = (source_conf + target_conf) / 2
        
        base_confidence += avg_conf * 0.3
        
        # Boost for verified entities
        if source_entity.get("is_verified") and target_entity.get("is_verified"):
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    def _calculate_document_reliability(self, document: Dict) -> float:
        """Calculate document reliability score"""
        
        score = 0.5  # Base score
        
        # File type reliability
        file_type = document.get("file_type", "").lower()
        if file_type in ["pdf", "doc", "docx"]:
            score += 0.2
        elif file_type in ["txt", "csv"]:
            score += 0.1
        
        # File size (reasonable size gets bonus)
        file_size = document.get("file_size", 0)
        if 1000 < file_size < 10000000:  # 1KB to 10MB
            score += 0.1
        
        # Processing success rate
        if document.get("processing_status") == "completed":
            score += 0.1
        
        # Upload date (recent is better)
        upload_date = document.get("uploaded_at")
        if upload_date:
            try:
                upload_datetime = datetime.fromisoformat(upload_date.replace("Z", "+00:00"))
                days_old = (datetime.now() - upload_datetime.replace(tzinfo=None)).days
                if days_old < 30:
                    score += 0.1
            except:
                pass
        
        return min(score, 1.0)
    
    def _extract_document_date(self, document: Dict) -> Optional[datetime]:
        """Extract date from document"""
        
        date_fields = ["uploaded_at", "created_at", "modified_at"]
        
        for field in date_fields:
            if field in document and document[field]:
                try:
                    return datetime.fromisoformat(document[field].replace("Z", "+00:00"))
                except:
                    continue
        
        return None
    
    def _analyze_schema_differences(self, source_entity: Dict, target_entity: Dict) -> List[Dict]:
        """Analyze schema differences and create transformation rules"""
        
        transformations = []
        
        source_props = source_entity.get("properties", {})
        target_props = target_entity.get("properties", {})
        
        # Common field mappings
        field_mappings = {
            "company": "organization_name",
            "corp": "organization_name",
            "org": "organization_name",
            "fname": "first_name",
            "lname": "last_name",
            "full_name": "name",
            "desc": "description",
            "addr": "address"
        }
        
        for source_field, target_field in field_mappings.items():
            if source_field in source_props and target_field in target_props:
                transformations.append({
                    "entity_id": source_entity["id"],
                    "transform_type": "normalize_properties",
                    "mapping_rules": {source_field: target_field}
                })
        
        return transformations
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level string"""
        
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def get_resolution_stats(self) -> Dict[str, Any]:
        """Get resolution statistics"""
        
        return {
            "total_resolved": self.resolution_stats['total_resolved'],
            "success_rate": self.resolution_stats['total_resolved'] / max(1, self.resolution_stats['total_resolved'] + self.resolution_stats['failed_resolutions']),
            "by_method": self.resolution_stats['by_method'],
            "by_confidence": self.resolution_stats['by_confidence'],
            "failed_resolutions": self.resolution_stats['failed_resolutions']
        }

