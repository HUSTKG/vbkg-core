import asyncio
import re
from collections import Counter, defaultdict
from typing import Dict, List, Set

from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import ConflictStatus, QualityDimension
from app.services.quality.base import QualityAssessor


class ConsistencyAssessor(QualityAssessor):
    """Assess data consistency based on conflicts, format patterns, and cross-field validation"""

    def get_dimension(self) -> QualityDimension:
        return QualityDimension.CONSISTENCY

    async def assess(
        self, total_entities: int = None, conflicts_pending: int = None, **kwargs
    ) -> float:
        """Assess consistency based on multiple factors"""
        supabase = await get_supabase()

        # Get all required data concurrently
        tasks = [
            self._get_conflict_consistency_score(
                supabase, total_entities, conflicts_pending
            ),
            self._get_format_consistency_score(supabase),
            self._get_naming_consistency_score(supabase),
            self._get_cross_field_consistency_score(supabase),
        ]

        conflict_score, format_score, naming_score, cross_field_score = (
            await asyncio.gather(*tasks)
        )

        # Weighted average of different consistency aspects
        weights = {
            "conflicts": 0.3,  # Conflicts are important but not everything
            "format": 0.25,  # Format consistency
            "naming": 0.25,  # Naming conventions
            "cross_field": 0.2,  # Cross-field validation
        }

        total_score = (
            conflict_score * weights["conflicts"]
            + format_score * weights["format"]
            + naming_score * weights["naming"]
            + cross_field_score * weights["cross_field"]
        )

        return min(1.0, max(0.0, total_score))

    async def _get_conflict_consistency_score(
        self, supabase, total_entities: int = None, conflicts_pending: int = None
    ) -> float:
        """Calculate consistency score based on conflicts (improved version)"""
        if total_entities is None or conflicts_pending is None:
            total_entities, conflicts_pending = await asyncio.gather(
                self._get_total_entities(supabase),
                self._get_pending_conflicts(supabase),
            )

        if total_entities == 0:
            return 1.0

        # More reasonable conflict ratio calculation
        conflict_ratio = conflicts_pending / total_entities

        # Use exponential decay instead of linear penalty
        # This gives more gradual scoring
        import math

        consistency_score = math.exp(-conflict_ratio * 3)  # Smoother penalty

        return max(0.0, min(1.0, consistency_score))

    async def _get_format_consistency_score(self, supabase) -> float:
        """Assess consistency of data formats (emails, phones, dates, etc.)"""
        entities = await self._get_entities_with_properties(supabase)
        if not entities:
            return 1.0

        format_scores = []

        # Group entities by type to check format consistency within types
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get("entity_type", "UNKNOWN")
            entities_by_type[entity_type].append(entity)

        for entity_type, type_entities in entities_by_type.items():
            type_score = self._calculate_type_format_consistency(type_entities)
            format_scores.append(type_score)

        return sum(format_scores) / len(format_scores) if format_scores else 1.0

    def _calculate_type_format_consistency(self, entities: List[Dict]) -> float:
        """Calculate format consistency for entities of the same type"""
        if len(entities) <= 1:
            return 1.0

        format_patterns = defaultdict(list)

        for entity in entities:
            properties = entity.get("properties", {})

            # Check common fields for format patterns
            for field, value in properties.items():
                if value and isinstance(value, str):
                    pattern = self._detect_format_pattern(field, value)
                    if pattern:
                        format_patterns[field].append(pattern)

        # Calculate consistency score for each field
        field_scores = []
        for field, patterns in format_patterns.items():
            if patterns:
                # Count pattern frequencies
                pattern_counts = Counter(patterns)
                most_common_count = pattern_counts.most_common(1)[0][1]
                consistency_ratio = most_common_count / len(patterns)
                field_scores.append(consistency_ratio)

        return sum(field_scores) / len(field_scores) if field_scores else 1.0

    def _detect_format_pattern(self, field_name: str, value: str) -> str:
        """Detect format patterns for common field types"""
        field_lower = field_name.lower()

        # Email patterns
        if "email" in field_lower:
            if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
                return "valid_email"
            return "invalid_email"

        # Phone patterns
        elif "phone" in field_lower or "mobile" in field_lower:
            # Remove common separators for pattern detection
            clean_phone = re.sub(r"[^\d+]", "", value)
            if len(clean_phone) >= 10:
                return f"phone_{len(clean_phone)}_digits"
            return "invalid_phone"

        # Date patterns
        elif "date" in field_lower or "birth" in field_lower:
            date_patterns = [
                (r"^\d{4}-\d{2}-\d{2}$", "yyyy-mm-dd"),
                (r"^\d{2}/\d{2}/\d{4}$", "mm/dd/yyyy"),
                (r"^\d{2}-\d{2}-\d{4}$", "mm-dd-yyyy"),
                (r"^\d{4}/\d{2}/\d{2}$", "yyyy/mm/dd"),
            ]
            for pattern, format_name in date_patterns:
                if re.match(pattern, value):
                    return format_name
            return "unknown_date_format"

        # ID patterns
        elif "id" in field_lower:
            if value.isdigit():
                return "numeric_id"
            elif re.match(r"^[A-Z]{2,3}\d+$", value):
                return "alpha_numeric_id"
            return "mixed_id"

        return None

    async def _get_naming_consistency_score(self, supabase) -> float:
        """Assess naming convention consistency"""
        entities = await self._get_entities_with_properties(supabase)
        if not entities:
            return 1.0

        naming_scores = []

        # Check field naming conventions
        all_field_names = set()
        for entity in entities:
            properties = entity.get("properties", {})
            all_field_names.update(properties.keys())

        if all_field_names:
            naming_score = self._calculate_naming_convention_score(all_field_names)
            naming_scores.append(naming_score)

        # Check entity name consistency
        name_consistency = self._calculate_entity_name_consistency(entities)
        naming_scores.append(name_consistency)

        return sum(naming_scores) / len(naming_scores) if naming_scores else 1.0

    def _calculate_naming_convention_score(self, field_names: Set[str]) -> float:
        """Calculate consistency of field naming conventions"""
        if not field_names:
            return 1.0

        convention_counts = {
            "snake_case": 0,
            "camelCase": 0,
            "PascalCase": 0,
            "kebab-case": 0,
            "UPPER_CASE": 0,
            "mixed": 0,
        }

        for name in field_names:
            convention = self._detect_naming_convention(name)
            convention_counts[convention] += 1

        # Calculate consistency ratio
        total = len(field_names)
        max_convention_count = max(convention_counts.values())

        return max_convention_count / total if total > 0 else 1.0

    def _detect_naming_convention(self, name: str) -> str:
        """Detect naming convention used"""
        if "_" in name and name.islower():
            return "snake_case"
        elif "_" in name and name.isupper():
            return "UPPER_CASE"
        elif "-" in name:
            return "kebab-case"
        elif name[0].isupper() and any(c.isupper() for c in name[1:]):
            return "PascalCase"
        elif name[0].islower() and any(c.isupper() for c in name[1:]):
            return "camelCase"
        else:
            return "mixed"

    def _calculate_entity_name_consistency(self, entities: List[Dict]) -> float:
        """Calculate consistency of entity naming within types"""
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get("entity_type", "UNKNOWN")
            properties = entity.get("properties", {})
            name = (
                properties.get("name")
                or properties.get("full_name")
                or properties.get("title")
            )
            if name:
                entities_by_type[entity_type].append(name)

        type_scores = []
        for entity_type, names in entities_by_type.items():
            if len(names) > 1:
                # Check naming pattern consistency within entity type
                patterns = [self._get_name_pattern(name) for name in names]
                pattern_counts = Counter(patterns)
                most_common_count = pattern_counts.most_common(1)[0][1]
                consistency_ratio = most_common_count / len(patterns)
                type_scores.append(consistency_ratio)

        return sum(type_scores) / len(type_scores) if type_scores else 1.0

    def _get_name_pattern(self, name: str) -> str:
        """Get naming pattern for entity names"""
        if not name:
            return "empty"

        # Basic patterns
        if name.isupper():
            return "UPPERCASE"
        elif name.islower():
            return "lowercase"
        elif name.istitle():
            return "Title Case"
        else:
            return "Mixed Case"

    async def _get_cross_field_consistency_score(self, supabase) -> float:
        """Assess consistency across related fields"""
        entities = await self._get_entities_with_properties(supabase)
        if not entities:
            return 1.0

        consistency_scores = []

        for entity in entities:
            properties = entity.get("properties", {})
            entity_score = self._validate_cross_field_consistency(properties)
            consistency_scores.append(entity_score)

        return (
            sum(consistency_scores) / len(consistency_scores)
            if consistency_scores
            else 1.0
        )

    def _validate_cross_field_consistency(self, properties: Dict) -> float:
        """Validate consistency between related fields"""
        validations = []

        # Date consistency checks
        birth_date = properties.get("date_of_birth")
        death_date = properties.get("date_of_death")
        if birth_date and death_date:
            # Simple check: death date should be after birth date
            try:
                # This is a simplified check - in reality you'd parse dates properly
                birth_year = int(birth_date[:4]) if len(birth_date) >= 4 else None
                death_year = int(death_date[:4]) if len(death_date) >= 4 else None
                if birth_year and death_year:
                    validations.append(death_year >= birth_year)
            except (ValueError, TypeError):
                validations.append(False)

        # Age consistency check
        age = properties.get("age")
        if age and birth_date:
            try:
                birth_year = int(birth_date[:4])
                current_year = 2025  # Or use current year
                expected_age = current_year - birth_year
                # Allow some tolerance for age calculation
                validations.append(abs(int(age) - expected_age) <= 1)
            except (ValueError, TypeError):
                validations.append(False)

        # Location consistency (country/city relationships)
        country = properties.get("country")
        city = properties.get("city")
        if country and city:
            # This would require a lookup table in real implementation
            # For now, just check they're both strings
            validations.append(isinstance(country, str) and isinstance(city, str))

        # If no validations were performed, assume consistent
        if not validations:
            return 1.0

        return sum(validations) / len(validations)

    async def _get_total_entities(self, supabase) -> int:
        """Get total count of active entities"""
        response = (
            await supabase.table("kg_entities")
            .select("*", count=CountMethod.exact)
            .eq("is_active", True)
            .execute()
        )
        return response.count or 0

    async def _get_pending_conflicts(self, supabase) -> int:
        """Get count of pending conflicts"""
        response = (
            await supabase.table("conflicts")
            .select("*", count=CountMethod.exact)
            .in_(
                "status",
                [ConflictStatus.DETECTED.value, ConflictStatus.UNDER_REVIEW.value],
            )
            .execute()
        )
        return response.count or 0

    async def _get_entities_with_properties(self, supabase) -> List[Dict]:
        """Get all active entities with their properties"""
        response = (
            await supabase.table("kg_entities")
            .select("entity_type, properties")
            .eq("is_active", True)
            .execute()
        )
        return response.data

    async def get_consistency_metrics(self) -> Dict:
        """Get detailed consistency metrics for monitoring"""
        supabase = await get_supabase()

        # Get individual component scores
        conflict_score = await self._get_conflict_consistency_score(supabase)
        format_score = await self._get_format_consistency_score(supabase)
        naming_score = await self._get_naming_consistency_score(supabase)
        cross_field_score = await self._get_cross_field_consistency_score(supabase)

        # Get additional metrics
        total_entities = await self._get_total_entities(supabase)
        pending_conflicts = await self._get_pending_conflicts(supabase)

        return {
            "overall_consistency": await self.assess(),
            "conflict_consistency": round(conflict_score, 3),
            "format_consistency": round(format_score, 3),
            "naming_consistency": round(naming_score, 3),
            "cross_field_consistency": round(cross_field_score, 3),
            "total_entities": total_entities,
            "pending_conflicts": pending_conflicts,
            "conflict_ratio": (
                round(pending_conflicts / total_entities, 4)
                if total_entities > 0
                else 0
            ),
        }
