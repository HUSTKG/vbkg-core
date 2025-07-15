import json
from typing import Dict, List, Optional

from app.core.llm_client import get_llm_client
from app.schemas.conflict_resolution import ConflictCreate, ConflictSeverity

from .base import BaseConflictService


class LLMAnalysisService(BaseConflictService):
    """Service for LLM-enhanced conflict analysis"""

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = get_llm_client()

    async def enhance_conflicts_with_llm(self, conflicts: List[ConflictCreate]):
        """Enhance high-priority conflicts with LLM analysis"""

        if not conflicts:
            return

        # Filter high-priority conflicts
        high_priority_conflicts = [
            c
            for c in conflicts
            if c.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        ]

        # Process top conflicts only to manage LLM costs
        for conflict in high_priority_conflicts[:5]:
            try:
                enhanced_analysis = await self._get_llm_conflict_analysis(conflict)

                if enhanced_analysis:
                    self._apply_llm_enhancements(conflict, enhanced_analysis)

            except Exception as e:
                self.logger.warning(
                    f"LLM enhancement failed for conflict {conflict}: {e}"
                )

    async def _get_llm_conflict_analysis(
        self, conflict: ConflictCreate
    ) -> Optional[Dict]:
        """Get LLM analysis for a specific conflict"""

        # Get entity details
        entity1, entity2 = await self._get_conflict_entities(conflict)

        if not entity1 or not entity2:
            return None

        prompt = self._build_analysis_prompt(conflict, entity1, entity2)

        try:
            response = await self.llm_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in knowledge graph conflict analysis. Provide precise, actionable insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return None

    async def _get_conflict_entities(self, conflict: ConflictCreate) -> tuple:
        """Get entity details for conflict analysis"""

        supabase = await self.get_supabase()

        entity1_response, entity2_response = await asyncio.gather(
            supabase.table("kg_entities")
            .select("*")
            .eq("id", conflict.source_entity_id)
            .maybe_single()
            .execute(),
            supabase.table("kg_entities")
            .select("*")
            .eq("id", conflict.target_entity_id)
            .maybe_single()
            .execute(),
        )

        return entity1_response.data, entity2_response.data

    def _build_analysis_prompt(
        self, conflict: ConflictCreate, entity1: Dict, entity2: Dict
    ) -> str:
        """Build LLM analysis prompt"""

        return f"""
        Analyze this knowledge graph conflict:

        Conflict Type: {conflict.conflict_type.value}
        Similarity Score: {conflict.confidence_score:.3f}

        Entity 1:
        - Text: "{entity1['entity_text']}"
        - Type: {entity1['entity_type']}
        - Properties: {json.dumps(entity1.get('properties', {}), indent=2)}

        Entity 2:  
        - Text: "{entity2['entity_text']}"
        - Type: {entity2['entity_type']}
        - Properties: {json.dumps(entity2.get('properties', {}), indent=2)}

        Provide analysis in JSON format:
        {{
            "is_real_conflict": true/false,
            "confidence_adjustment": -0.1 to +0.1,
            "reasoning": "detailed explanation",
            "recommended_action": "merge|keep_both|manual_review",
            "key_differences": ["list of important differences"],
            "similarity_factors": ["factors contributing to similarity"]
        }}
        """

    def _apply_llm_enhancements(self, conflict: ConflictCreate, analysis: Dict):
        """Apply LLM analysis to conflict"""

        if not conflict.context_data:
            conflict.context_data = {}

        conflict.context_data["llm_analysis"] = analysis

        # Adjust confidence based on LLM analysis
        if analysis.get("confidence_adjustment"):
            new_confidence = min(
                1.0,
                max(
                    0.0,
                    conflict.confidence_score + analysis["confidence_adjustment"],
                ),
            )
            conflict.confidence_score = new_confidence
