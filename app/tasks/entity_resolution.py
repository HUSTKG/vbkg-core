import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


class EntityResolutionTask:
    """
    Task for entity resolution using various strategies with Vietnamese support
    """

    def __init__(self):
        pass

    async def resolve_entities(
        self,
        entities: List[Dict[str, Any]],
        resolution_strategy: str = "fuzzy_match",
        similarity_threshold: float = 0.8,
        clustering_method: str = "single_linkage",
        auto_save: bool = True,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve entities using the specified strategy

        Args:
            entities: List of entities to resolve
            resolution_strategy: Strategy to use (fuzzy_match, exact_match, semantic_similarity)
            similarity_threshold: Similarity threshold for clustering
            clustering_method: Clustering method
            auto_save: Whether to save results automatically
            user_id: User performing resolution

        Returns:
            Dictionary containing resolution results
        """
        try:
            logger.info(f"Starting entity resolution task {entities}")
            if not entities:
                return {
                    "resolved_entities": [],
                    "entity_clusters": [],
                    "resolution_stats": {
                        "input_entities": 0,
                        "resolved_entities": 0,
                        "clusters_formed": 0,
                        "resolution_strategy": resolution_strategy,
                    },
                    "success": True,
                }

            logger.info(
                f"Starting entity resolution with strategy: {resolution_strategy}"
            )
            logger.debug(f"Input entities: {entities}")
            # Perform entity resolution based on strategy

            if resolution_strategy == "fuzzy_match":
                logger.info("Using fuzzy match resolution strategy")
                resolved_entities, entity_clusters = await self._fuzzy_match_resolution(
                    entities, similarity_threshold, clustering_method
                )
            elif resolution_strategy == "exact_match":
                resolved_entities, entity_clusters = await self._exact_match_resolution(
                    entities
                )
            elif resolution_strategy == "semantic_similarity":
                resolved_entities, entity_clusters = (
                    await self._semantic_similarity_resolution(
                        entities, similarity_threshold
                    )
                )
            else:
                # Default to fuzzy match
                resolved_entities, entity_clusters = await self._fuzzy_match_resolution(
                    entities, similarity_threshold, clustering_method
                )

            # Auto-save results if requested
            saved_data = None
            if auto_save:
                saved_data = await self._save_resolution_results(
                    resolved_entities, entity_clusters, user_id
                )

            result = {
                "resolved_entities": resolved_entities,
                "entity_clusters": entity_clusters,
                "resolution_stats": {
                    "input_entities": len(entities),
                    "resolved_entities": len(resolved_entities),
                    "clusters_formed": len(entity_clusters),
                    "resolution_strategy": resolution_strategy,
                    "similarity_threshold": similarity_threshold,
                },
                "saved_data": saved_data,
                "success": True,
            }

            logger.info(
                f"Entity resolution completed: {len(entities)} -> {len(resolved_entities)} entities"
            )
            return result

        except Exception as e:
            logger.error(f"Error in entity resolution: {e}")
            return {
                "resolved_entities": [],
                "entity_clusters": [],
                "error": str(e),
                "success": False,
            }

    async def _fuzzy_match_resolution(
        self, entities: List[Dict[str, Any]], threshold: float, clustering_method: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using fuzzy string matching with Vietnamese support"""
        from difflib import SequenceMatcher

        # Calculate similarity matrix
        n = len(entities)
        similarity_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        logger.info(
            f"Calculating similarity matrix for {n} entities with threshold {threshold}"
        )

        for i in range(n):
            for j in range(i + 1, n):
                text1 = self._normalize_vietnamese_text(
                    entities[i].get("text", entities[i].get("entity_text", ""))
                )
                text2 = self._normalize_vietnamese_text(
                    entities[j].get("text", entities[j].get("entity_text", ""))
                )

                # Check if entities are of the same type
                type1 = entities[i].get("entity_type", "")
                type2 = entities[j].get("entity_type", "")
                logger.debug(
                    f"Comparing entities {i} and {j}: "
                    f"text1='{text1}', text2='{text2}', type1='{type1}', type2='{type2}'"
                )

                if type1 == type2:
                    similarity = SequenceMatcher(None, text1, text2).ratio()
                    similarity_matrix[i][j] = similarity
                    similarity_matrix[j][i] = similarity

        # Form clusters based on similarity threshold
        clusters = []
        assigned = set()

        for i in range(n):
            if i in assigned:
                continue

            cluster = [i]
            assigned.add(i)

            for j in range(i + 1, n):
                if j not in assigned and similarity_matrix[i][j] >= threshold:
                    cluster.append(j)
                    assigned.add(j)

            if len(cluster) > 1:
                clusters.append(cluster)

        logger.info(f"Formed {len(clusters)} clusters from {n} entities")
        # Create resolved entities and cluster information
        resolved_entities = []
        entity_clusters = []

        # Process clusters
        for cluster_indices in clusters:
            cluster_entities = [entities[i] for i in cluster_indices]

            # Select the entity with highest confidence as the canonical one
            canonical_entity = max(
                cluster_entities, key=lambda e: e.get("confidence", 0)
            )
            canonical_entity = canonical_entity.copy()
            canonical_entity["cluster_id"] = len(entity_clusters)
            canonical_entity["cluster_size"] = len(cluster_entities)
            canonical_entity["is_resolved"] = True

            resolved_entities.append(canonical_entity)

            entity_clusters.append(
                {
                    "cluster_id": len(entity_clusters),
                    "canonical_entity": canonical_entity,
                    "cluster_entities": cluster_entities,
                    "cluster_size": len(cluster_entities),
                    "avg_similarity": sum(
                        [
                            similarity_matrix[cluster_indices[i]][cluster_indices[j]]
                            for i in range(len(cluster_indices))
                            for j in range(i + 1, len(cluster_indices))
                        ]
                    )
                    / max(1, len(cluster_indices) * (len(cluster_indices) - 1) // 2),
                }
            )

        logger.debug(f"Resolved {len(resolved_entities)} entities from clusters")

        # Add unclustered entities
        for i, entity in enumerate(entities):
            if not any(i in cluster for cluster in clusters):
                entity_copy = entity.copy()
                entity_copy["cluster_id"] = None
                entity_copy["cluster_size"] = 1
                entity_copy["is_resolved"] = False
                resolved_entities.append(entity_copy)

        logger.info(
            f"Fuzzy match resolution completed: {len(entities)} input entities, "
            f"{resolved_entities} resolved entities, {entity_clusters} clusters formed"
        )

        return resolved_entities, entity_clusters

    async def _exact_match_resolution(
        self, entities: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using exact text matching with Vietnamese normalization"""
        entity_map = {}
        clusters = []

        for entity in entities:
            text = self._normalize_vietnamese_text(
                entity.get("text", entity.get("entity_text", ""))
            )
            entity_type = entity.get("entity_type", "")
            key = f"{text}_{entity_type}"

            if key in entity_map:
                entity_map[key].append(entity)
            else:
                entity_map[key] = [entity]

        resolved_entities = []
        for key, entity_list in entity_map.items():
            if len(entity_list) > 1:
                # Create cluster
                canonical_entity = max(
                    entity_list, key=lambda e: e.get("confidence", 0)
                )
                canonical_entity = canonical_entity.copy()
                canonical_entity["cluster_id"] = len(clusters)
                canonical_entity["cluster_size"] = len(entity_list)
                canonical_entity["is_resolved"] = True

                clusters.append(
                    {
                        "cluster_id": len(clusters),
                        "canonical_entity": canonical_entity,
                        "cluster_entities": entity_list,
                        "cluster_size": len(entity_list),
                        "match_type": "exact",
                    }
                )

                resolved_entities.append(canonical_entity)
            else:
                # Single entity
                entity_copy = entity_list[0].copy()
                entity_copy["cluster_id"] = None
                entity_copy["cluster_size"] = 1
                entity_copy["is_resolved"] = False
                resolved_entities.append(entity_copy)

        return resolved_entities, clusters

    async def _semantic_similarity_resolution(
        self, entities: List[Dict[str, Any]], threshold: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using semantic similarity (if embeddings are available)"""
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            from app.nlp.embeddings import get_embedding_service

            # Get embedding service
            embedding_service = get_embedding_service()

            # Get embeddings for all entities
            entity_texts = [e.get("text", e.get("entity_text", "")) for e in entities]
            embeddings = await embedding_service.get_embeddings(entity_texts)

            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(embeddings)

            # Form clusters based on similarity threshold
            n = len(entities)
            clusters = []
            assigned = set()

            for i in range(n):
                if i in assigned:
                    continue

                cluster = [i]
                assigned.add(i)

                for j in range(i + 1, n):
                    if (
                        j not in assigned
                        and similarity_matrix[i][j] >= threshold
                        and entities[i].get("entity_type")
                        == entities[j].get("entity_type")
                    ):
                        cluster.append(j)
                        assigned.add(j)

                if len(cluster) > 1:
                    clusters.append(cluster)

            # Create resolved entities and clusters
            resolved_entities = []
            entity_clusters = []

            for cluster_indices in clusters:
                cluster_entities = [entities[i] for i in cluster_indices]
                canonical_entity = max(
                    cluster_entities, key=lambda e: e.get("confidence", 0)
                )
                canonical_entity = canonical_entity.copy()
                canonical_entity["cluster_id"] = len(entity_clusters)
                canonical_entity["cluster_size"] = len(cluster_entities)
                canonical_entity["is_resolved"] = True

                resolved_entities.append(canonical_entity)
                entity_clusters.append(
                    {
                        "cluster_id": len(entity_clusters),
                        "canonical_entity": canonical_entity,
                        "cluster_entities": cluster_entities,
                        "cluster_size": len(cluster_entities),
                        "avg_similarity": (
                            np.mean(
                                [
                                    similarity_matrix[cluster_indices[i]][
                                        cluster_indices[j]
                                    ]
                                    for i in range(len(cluster_indices))
                                    for j in range(i + 1, len(cluster_indices))
                                ]
                            )
                            if len(cluster_indices) > 1
                            else 1.0
                        ),
                    }
                )

            # Add unclustered entities
            for i, entity in enumerate(entities):
                if not any(i in cluster for cluster in clusters):
                    entity_copy = entity.copy()
                    entity_copy["cluster_id"] = None
                    entity_copy["cluster_size"] = 1
                    entity_copy["is_resolved"] = False
                    resolved_entities.append(entity_copy)

            return resolved_entities, entity_clusters

        except Exception as e:
            logger.warning(
                f"Semantic similarity resolution failed, falling back to fuzzy match: {e}"
            )
            return await self._fuzzy_match_resolution(
                entities, threshold, "single_linkage"
            )

    def _normalize_vietnamese_text(self, text: str) -> str:
        """Normalize Vietnamese text for comparison"""
        import re

        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r"^(ông|bà|anh|chị|em|cô|chú|bác)\s+", "", text)
        text = re.sub(r"\s+(ạ|à|ơi|nhé)$", "", text)

        # Normalize common banking terms
        text = text.replace("tk", "tài khoản")
        text = text.replace("nh", "ngân hàng")
        text = text.replace("kh", "khách hàng")

        return text

    async def _save_resolution_results(
        self,
        resolved_entities: List[Dict[str, Any]],
        entity_clusters: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save resolution results to database"""
        try:
            supabase = await get_supabase()

            # Save entity clusters
            cluster_ids = []
            for cluster in entity_clusters:
                cluster_data = {
                    "canonical_entity_id": cluster["canonical_entity"].get("id"),
                    "cluster_size": cluster["cluster_size"],
                    "confidence_score": cluster.get("avg_similarity", 0.0),
                    "resolution_method": cluster.get("match_type", "fuzzy"),
                    "entity_ids": [
                        e.get("id") for e in cluster["cluster_entities"]
                    ],
                    "created_by": user_id,
                }

                response = (
                    await supabase.from_("entity_clusters")
                    .insert(cluster_data)
                    .execute()
                )
                if response.data:
                    cluster_ids.append(response.data[0]["id"])

            # Update entities with cluster information
            entity_updates = []
            for entity in resolved_entities:
                if entity.get("cluster_id") is not None:
                    entity_updates.append(
                        {
                            "entity_id": entity.get("id"),
                            "cluster_id": entity.get("cluster_id"),
                            "is_resolved": entity.get("is_resolved", False),
                        }
                    )

            return {
                "clusters_saved": len(cluster_ids),
                "entities_updated": len(entity_updates),
                "cluster_ids": cluster_ids,
            }

        except Exception as e:
            logger.error(f"Error saving resolution results: {e}")
            return {"error": str(e)}

    async def get_resolution_statistics(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics about entity resolution"""
        try:
            supabase = await get_supabase()

            # Get cluster statistics
            cluster_response = (
                await supabase.from_("entity_clusters").select("*").execute()
            )
            clusters = cluster_response.data

            # Get entity statistics
            entity_response = await supabase.from_("kg_entities").select("*").execute()
            entities = entity_response.data

            total_entities = len(entities)
            clustered_entities = len([e for e in entities if e.get("cluster_id")])
            total_clusters = len(clusters)

            # Calculate cluster size distribution
            cluster_sizes = [c.get("cluster_size", 1) for c in clusters]
            avg_cluster_size = (
                sum(cluster_sizes) / len(cluster_sizes) if cluster_sizes else 0
            )

            return {
                "total_entities": total_entities,
                "clustered_entities": clustered_entities,
                "unclustered_entities": total_entities - clustered_entities,
                "total_clusters": total_clusters,
                "avg_cluster_size": avg_cluster_size,
                "clustering_percentage": (
                    (clustered_entities / total_entities * 100)
                    if total_entities > 0
                    else 0
                ),
                "domain": domain,
            }

        except Exception as e:
            logger.error(f"Error getting resolution statistics: {e}")
            return {}
