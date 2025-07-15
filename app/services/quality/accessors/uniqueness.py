import asyncio
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, List, Set, Tuple

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.base import QualityAssessor


class UniquenessAssessor(QualityAssessor):
    """Assess data uniqueness by detecting duplicates"""

    def get_dimension(self) -> QualityDimension:
        return QualityDimension.UNIQUENESS

    async def assess(self, **kwargs) -> float:
        """Assess uniqueness by detecting duplicates"""
        supabase = await get_supabase()

        entities = await self._get_all_entities(supabase)
        if len(entities) <= 1:
            return 1.0

        # Detect duplicates using multiple strategies
        duplicate_pairs = await self._detect_all_duplicates(entities)

        if not duplicate_pairs:
            return 1.0

        # Calculate uniqueness score
        # Score decreases based on number of duplicate pairs found
        total_entities = len(entities)
        unique_duplicates = self._count_unique_duplicates(duplicate_pairs)

        # Calculate score: entities that are NOT part of duplicates / total entities
        entities_in_duplicates = len(unique_duplicates)
        unique_entities = total_entities - entities_in_duplicates

        uniqueness_score = (
            unique_entities / total_entities if total_entities > 0 else 1.0
        )

        print(duplicate_pairs[0])

        return max(0.0, min(1.0, uniqueness_score))

    async def _detect_all_duplicates(
        self, entities: List[Dict]
    ) -> List[Tuple[Dict, Dict, float]]:
        """Detect duplicates using multiple strategies"""
        all_duplicates = []

        # Group entities by type for more efficient comparison
        entities_by_type = defaultdict(list)
        for entity in entities:
            entity_type = entity.get("entity_type", "UNKNOWN")
            entities_by_type[entity_type].append(entity)

        # Detect duplicates within each entity type
        for entity_type, type_entities in entities_by_type.items():
            type_duplicates = await self._detect_type_duplicates(
                entity_type, type_entities
            )
            all_duplicates.extend(type_duplicates)

        # Cross-type duplicate detection for certain cases
        cross_type_duplicates = await self._detect_cross_type_duplicates(entities)
        all_duplicates.extend(cross_type_duplicates)

        return all_duplicates

    async def _detect_type_duplicates(
        self, entity_type: str, entities: List[Dict]
    ) -> List[Tuple[Dict, Dict, float]]:
        """Detect duplicates within the same entity type"""
        duplicates = []

        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]
                similarity = self._calculate_entity_similarity(
                    entity1, entity2, entity_type
                )

                # Threshold varies by entity type
                threshold = self._get_similarity_threshold(entity_type)

                if similarity >= threshold:
                    duplicates.append((entity1, entity2, similarity))

        return duplicates

    async def _detect_cross_type_duplicates(
        self, entities: List[Dict]
    ) -> List[Tuple[Dict, Dict, float]]:
        """Detect duplicates across different entity types (rare cases)"""
        duplicates = []

        # Only check specific cross-type scenarios
        # Example: PERSON vs ORGANIZATION (when person name matches org name)

        persons = [e for e in entities if e.get("entity_type") == "PERSON"]
        orgs = [e for e in entities if e.get("entity_type") == "ORGANIZATION"]

        for person in persons:
            for org in orgs:
                # Check if person name matches organization name (potential duplicate)
                person_name = self._extract_primary_name(person)
                org_name = self._extract_primary_name(org)

                if person_name and org_name:
                    similarity = self._calculate_string_similarity(
                        person_name, org_name
                    )
                    if similarity >= 0.9:  # High threshold for cross-type
                        duplicates.append((person, org, similarity))

        return duplicates

    def _calculate_entity_similarity(
        self, entity1: Dict, entity2: Dict, entity_type: str
    ) -> float:
        """Calculate similarity between two entities of the same type"""
        if entity_type == "PERSON":
            return self._calculate_person_similarity(entity1, entity2)
        elif entity_type == "ORGANIZATION":
            return self._calculate_organization_similarity(entity1, entity2)
        elif entity_type == "LOCATION":
            return self._calculate_location_similarity(entity1, entity2)
        elif entity_type == "EVENT":
            return self._calculate_event_similarity(entity1, entity2)
        else:
            return self._calculate_generic_similarity(entity1, entity2)

    def _calculate_person_similarity(self, person1: Dict, person2: Dict) -> float:
        """Calculate similarity between two person entities"""
        props1 = person1.get("properties", {})
        props2 = person2.get("properties", {})

        scores = []
        weights = {}

        # Name similarity (highest weight)
        name1 = props1.get("full_name") or props1.get("name", "")
        name2 = props2.get("full_name") or props2.get("name", "")
        if name1 and name2:
            name_sim = self._calculate_name_similarity(name1, name2)
            scores.append(name_sim)
            weights[len(scores) - 1] = 0.4

        # Email similarity (very high weight - should be unique)
        email1 = props1.get("email", "")
        email2 = props2.get("email", "")
        if email1 and email2:
            email_sim = 1.0 if email1.lower() == email2.lower() else 0.0
            scores.append(email_sim)
            weights[len(scores) - 1] = 0.3

        # Phone similarity (high weight)
        phone1 = self._normalize_phone(props1.get("phone", ""))
        phone2 = self._normalize_phone(props2.get("phone", ""))
        if phone1 and phone2:
            phone_sim = 1.0 if phone1 == phone2 else 0.0
            scores.append(phone_sim)
            weights[len(scores) - 1] = 0.2

        # Date of birth similarity
        dob1 = props1.get("date_of_birth", "")
        dob2 = props2.get("date_of_birth", "")
        if dob1 and dob2:
            dob_sim = 1.0 if dob1 == dob2 else 0.0
            scores.append(dob_sim)
            weights[len(scores) - 1] = 0.1

        # Calculate weighted average
        if not scores:
            return 0.0

        total_weight = sum(weights.values())
        if total_weight == 0:
            return sum(scores) / len(scores)

        weighted_sum = sum(
            score * weights.get(i, 1.0) for i, score in enumerate(scores)
        )
        return weighted_sum / total_weight

    def _calculate_organization_similarity(self, org1: Dict, org2: Dict) -> float:
        """Calculate similarity between two organization entities"""
        props1 = org1.get("properties", {})
        props2 = org2.get("properties", {})

        scores = []
        weights = {}

        # Organization name similarity
        name1 = props1.get("name", "")
        name2 = props2.get("name", "")
        if name1 and name2:
            # Normalize organization names (remove common suffixes)
            norm_name1 = self._normalize_org_name(name1)
            norm_name2 = self._normalize_org_name(name2)
            name_sim = self._calculate_string_similarity(norm_name1, norm_name2)
            scores.append(name_sim)
            weights[len(scores) - 1] = 0.5

        # Website similarity (should be unique)
        website1 = self._normalize_website(props1.get("website", ""))
        website2 = self._normalize_website(props2.get("website", ""))
        if website1 and website2:
            website_sim = 1.0 if website1 == website2 else 0.0
            scores.append(website_sim)
            weights[len(scores) - 1] = 0.3

        # Address/Location similarity
        addr1 = props1.get("address", "") or props1.get("headquarters", "")
        addr2 = props2.get("address", "") or props2.get("headquarters", "")
        if addr1 and addr2:
            addr_sim = self._calculate_string_similarity(addr1, addr2)
            scores.append(addr_sim)
            weights[len(scores) - 1] = 0.2

        if not scores:
            return 0.0

        total_weight = sum(weights.values())
        if total_weight == 0:
            return sum(scores) / len(scores)

        weighted_sum = sum(
            score * weights.get(i, 1.0) for i, score in enumerate(scores)
        )
        return weighted_sum / total_weight

    def _calculate_location_similarity(self, loc1: Dict, loc2: Dict) -> float:
        """Calculate similarity between two location entities"""
        props1 = loc1.get("properties", {})
        props2 = loc2.get("properties", {})

        scores = []

        # Name similarity
        name1 = props1.get("name", "")
        name2 = props2.get("name", "")
        if name1 and name2:
            scores.append(self._calculate_string_similarity(name1, name2))

        # Coordinates similarity (if available)
        coords1 = props1.get("coordinates", "")
        coords2 = props2.get("coordinates", "")
        if coords1 and coords2:
            coords_sim = 1.0 if coords1 == coords2 else 0.0
            scores.append(coords_sim)

        # Country/Region similarity
        country1 = props1.get("country", "")
        country2 = props2.get("country", "")
        if country1 and country2:
            country_sim = 1.0 if country1.lower() == country2.lower() else 0.0
            scores.append(country_sim)

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_event_similarity(self, event1: Dict, event2: Dict) -> float:
        """Calculate similarity between two event entities"""
        props1 = event1.get("properties", {})
        props2 = event2.get("properties", {})

        scores = []

        # Event name/title similarity
        name1 = props1.get("name", "") or props1.get("title", "")
        name2 = props2.get("name", "") or props2.get("title", "")
        if name1 and name2:
            scores.append(self._calculate_string_similarity(name1, name2))

        # Date similarity
        date1 = props1.get("date", "") or props1.get("start_date", "")
        date2 = props2.get("date", "") or props2.get("start_date", "")
        if date1 and date2:
            date_sim = 1.0 if date1 == date2 else 0.0
            scores.append(date_sim)

        # Location similarity
        location1 = props1.get("location", "") or props1.get("venue", "")
        location2 = props2.get("location", "") or props2.get("venue", "")
        if location1 and location2:
            scores.append(self._calculate_string_similarity(location1, location2))

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_generic_similarity(self, entity1: Dict, entity2: Dict) -> float:
        """Calculate similarity for entities without specific type logic"""
        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})

        # Get common properties
        common_props = set(props1.keys()) & set(props2.keys())
        if not common_props:
            return 0.0

        similarities = []
        for prop in common_props:
            val1, val2 = str(props1[prop]), str(props2[prop])
            if val1 and val2:
                similarities.append(self._calculate_string_similarity(val1, val2))

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between names (handles different formats)"""
        # Normalize names
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)

        # Exact match
        if norm1 == norm2:
            return 1.0

        # Check if one is contained in the other (nickname scenarios)
        if norm1 in norm2 or norm2 in norm1:
            return 0.8

        # Calculate string similarity
        return self._calculate_string_similarity(norm1, norm2)

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using SequenceMatcher"""
        return SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        # Remove extra whitespace, convert to lowercase
        normalized = re.sub(r"\s+", " ", name.strip().lower())

        # Remove common prefixes/suffixes
        prefixes = ["mr.", "mrs.", "ms.", "dr.", "prof."]
        suffixes = ["jr.", "sr.", "ii", "iii"]

        words = normalized.split()
        words = [w for w in words if w not in prefixes and w not in suffixes]

        return " ".join(words)

    def _normalize_org_name(self, name: str) -> str:
        """Normalize organization name for comparison"""
        normalized = name.lower().strip()

        # Remove common business suffixes
        suffixes = [
            "inc.",
            "inc",
            "corp.",
            "corp",
            "ltd.",
            "ltd",
            "llc",
            "llp",
            "co.",
            "co",
            "company",
            "corporation",
            "limited",
            "incorporated",
        ]

        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)].strip()
                break

        return normalized

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison"""
        if not phone:
            return ""

        # Extract only digits
        digits = re.sub(r"[^\d]", "", phone)

        # Remove country code if present (assuming US/international formats)
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]

        return digits

    def _normalize_website(self, website: str) -> str:
        """Normalize website URL for comparison"""
        if not website:
            return ""

        # Remove protocol and www
        normalized = website.lower().strip()
        normalized = re.sub(r"^https?://", "", normalized)
        normalized = re.sub(r"^www\.", "", normalized)
        normalized = normalized.rstrip("/")

        return normalized

    def _extract_primary_name(self, entity: Dict) -> str:
        """Extract primary name from entity for comparison"""
        props = entity.get("properties", {})
        return props.get("full_name") or props.get("name") or props.get("title") or ""

    def _get_similarity_threshold(self, entity_type: str) -> float:
        """Get similarity threshold for duplicate detection by entity type"""
        thresholds = {
            "PERSON": 0.85,  # High threshold for people (names can vary)
            "ORGANIZATION": 0.80,  # Medium-high for organizations
            "LOCATION": 0.90,  # High for locations (should be more exact)
            "EVENT": 0.85,  # High for events
            "PRODUCT": 0.75,  # Lower for products (more variation)
        }
        return thresholds.get(entity_type, 0.80)  # Default threshold

    def _count_unique_duplicates(
        self, duplicate_pairs: List[Tuple[Dict, Dict, float]]
    ) -> Set[str]:
        """Count unique entities that are part of duplicates"""
        duplicate_entities = set()

        for entity1, entity2, _ in duplicate_pairs:
            # Use entity ID or a unique identifier
            id1 = entity1.get("id") or str(hash(frozenset(entity1.items())))
            id2 = entity2.get("id") or str(hash(frozenset(entity2.items())))
            duplicate_entities.add(id1)
            duplicate_entities.add(id2)

        return duplicate_entities

    async def _get_all_entities(self, supabase) -> List[Dict]:
        """Get all active entities for uniqueness assessment"""
        response = (
            await supabase.table("kg_entities")
            .select("id, entity_type, properties, confidence, is_verified")
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def get_uniqueness_metrics(self) -> Dict:
        """Get detailed uniqueness metrics for monitoring"""
        supabase = await get_supabase()
        entities = await self._get_all_entities(supabase)

        if not entities:
            return {
                "total_entities": 0,
                "duplicate_pairs": 0,
                "unique_entities": 0,
                "uniqueness_score": 1.0,
                "duplicates_by_type": {},
                "similarity_distribution": {},
            }

        duplicate_pairs = await self._detect_all_duplicates(entities)
        unique_duplicates = self._count_unique_duplicates(duplicate_pairs)

        # Group duplicates by entity type
        duplicates_by_type = defaultdict(int)
        similarity_scores = []

        for entity1, entity2, similarity in duplicate_pairs:
            type1 = entity1.get("entity_type", "UNKNOWN")
            type2 = entity2.get("entity_type", "UNKNOWN")

            if type1 == type2:
                duplicates_by_type[type1] += 1
            else:
                duplicates_by_type["CROSS_TYPE"] += 1

            similarity_scores.append(similarity)

        # Calculate similarity distribution
        similarity_distribution = {}
        if similarity_scores:
            similarity_distribution = {
                "min": round(min(similarity_scores), 3),
                "max": round(max(similarity_scores), 3),
                "avg": round(sum(similarity_scores) / len(similarity_scores), 3),
                "high_similarity_count": len(
                    [s for s in similarity_scores if s >= 0.9]
                ),
                "medium_similarity_count": len(
                    [s for s in similarity_scores if 0.7 <= s < 0.9]
                ),
                "low_similarity_count": len([s for s in similarity_scores if s < 0.7]),
            }

        uniqueness_score = await self.assess()

        return {
            "total_entities": len(entities),
            "duplicate_pairs": len(duplicate_pairs),
            "entities_in_duplicates": len(unique_duplicates),
            "unique_entities": len(entities) - len(unique_duplicates),
            "uniqueness_score": round(uniqueness_score, 3),
            "duplicate_percentage": (
                round((len(unique_duplicates) / len(entities)) * 100, 2)
                if entities
                else 0
            ),
            "duplicates_by_type": dict(duplicates_by_type),
            "similarity_distribution": similarity_distribution,
        }
