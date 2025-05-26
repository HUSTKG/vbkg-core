import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.schemas.conflict_resolution import KGEdit, KGEditAction, KGEditResult
from app.services.user import UserService
from app.utils.neo4j import get_neo4j_driver

logger = logging.getLogger(__name__)


class KnowledgeGraphEditor:
    """Service for direct editing of knowledge graph with validation and rollback"""

    def __init__(self):
        self.change_log = []
        self.user_service = UserService()

    async def apply_edit(
        self, edit: KGEdit, user_id: str, validate_permissions: bool = True
    ) -> KGEditResult:
        """Apply a direct edit to the knowledge graph"""

        if validate_permissions and not await self._validate_edit_permissions(
            user_id, edit.action
        ):
            raise PermissionError("User does not have permission for this edit action")

        # Validate edit before applying
        if edit.validate_before_apply:
            validation_errors = await self._validate_edit(edit)
            if validation_errors:
                return KGEditResult(
                    success=False,
                    applied_changes=[],
                    validation_errors=validation_errors,
                )

        # Create rollback information before applying changes
        rollback_info = await self._create_rollback_info(edit)

        try:
            # Apply the edit
            applied_changes = await self._apply_edit_action(edit, user_id)

            # Log the change
            await self._log_change(edit, user_id, applied_changes)

            await self.user_service._log_user_activity(
                user_id=user_id,
                action="apply_kg_edit",
                details={
                    "edit_action": edit.action.value,
                    "applied_changes": applied_changes,
                    "reason": edit.reason,
                },
            )

            return KGEditResult(
                success=True,
                applied_changes=applied_changes,
                rollback_info=rollback_info,
            )

        except Exception as e:
            logger.error(f"Failed to apply edit: {e}")
            return KGEditResult(
                success=False,
                applied_changes=[],
                validation_errors=[str(e)],
                rollback_info=rollback_info,
            )

    async def _apply_edit_action(
        self, edit: KGEdit, user_id: str
    ) -> List[Dict[str, Any]]:
        """Apply the specific edit action"""

        action = edit.action
        applied_changes = []

        if action == KGEditAction.CREATE_ENTITY:
            result = await self._create_entity(edit.entity_data, user_id)
            applied_changes.append(
                {"action": "create_entity", "entity_id": result["id"]}
            )

        elif action == KGEditAction.UPDATE_ENTITY:
            result = await self._update_entity(edit.entity_data, user_id)
            applied_changes.append(
                {
                    "action": "update_entity",
                    "entity_id": result["id"],
                    "changes": result["changes"],
                }
            )

        elif action == KGEditAction.DELETE_ENTITY:
            result = await self._delete_entity(edit.entity_data["id"], user_id)
            applied_changes.append(
                {"action": "delete_entity", "entity_id": edit.entity_data["id"]}
            )

        elif action == KGEditAction.MERGE_ENTITIES:
            result = await self._merge_entities_direct(edit.entity_data, user_id)
            applied_changes.extend(result["changes"])

        elif action == KGEditAction.CREATE_RELATIONSHIP:
            result = await self._create_relationship(edit.relationship_data, user_id)
            applied_changes.append(
                {"action": "create_relationship", "relationship_id": result["id"]}
            )

        elif action == KGEditAction.UPDATE_RELATIONSHIP:
            result = await self._update_relationship(edit.relationship_data, user_id)
            applied_changes.append(
                {"action": "update_relationship", "relationship_id": result["id"]}
            )

        elif action == KGEditAction.DELETE_RELATIONSHIP:
            result = await self._delete_relationship(
                edit.relationship_data["id"], user_id
            )
            applied_changes.append(
                {
                    "action": "delete_relationship",
                    "relationship_id": edit.relationship_data["id"],
                }
            )

        elif action == KGEditAction.BULK_UPDATE:
            result = await self._apply_bulk_update(edit.bulk_data, user_id)
            applied_changes.extend(result["changes"])

        return applied_changes

    async def _create_entity(
        self, entity_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new entity in both PostgreSQL and Neo4j"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        # Generate embedding for entity text
        entity_text = entity_data["entity_text"]
        embedding = await get_text_embedding(entity_text)

        # Create entity in PostgreSQL
        postgres_data = {
            "entity_text": entity_text,
            "entity_type": entity_data["entity_type"],
            "properties": entity_data.get("properties", {}),
            "confidence": entity_data.get("confidence", 0.8),
            "embedding": embedding,
            "source_document_id": entity_data.get("source_document_id"),
            "is_verified": entity_data.get("is_verified", False),
            "created_by": user_id,
            "is_active": True,
        }

        pg_response = (
            await supabase.table("kg_entities").insert(postgres_data).execute()
        )
        entity_id = pg_response.data[0]["id"]

        # Create entity in Neo4j
        async with neo4j_driver.session() as session:
            neo4j_result = await session.run(
                """
                CREATE (e:Entity:{entity_type} {{
                    entity_id: $entity_id,
                    entity_text: $entity_text,
                    properties: $properties,
                    created_by: $created_by,
                    created_at: datetime()
                }})
                RETURN id(e) as neo4j_id
            """.format(
                    entity_type=entity_data["entity_type"]
                ),
                {
                    "entity_id": entity_id,
                    "entity_text": entity_text,
                    "properties": entity_data.get("properties", {}),
                    "created_by": user_id,
                },
            )

            record = await neo4j_result.single()
            neo4j_id = record["neo4j_id"]

            # Update PostgreSQL with Neo4j ID
            await supabase.table("kg_entities").update({"neo4j_id": str(neo4j_id)}).eq(
                "id", entity_id
            ).execute()

        return {"id": entity_id, "neo4j_id": neo4j_id}

    async def _update_entity(
        self, entity_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Update an existing entity"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        entity_id = entity_data["id"]

        # Get current entity data for comparison
        current_response = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", entity_id)
            .single()
            .execute()
        )
        current_entity = current_response.data

        if not current_entity:
            raise ValueError(f"Entity {entity_id} not found")

        # Prepare updates
        updates = {}
        changes = {}

        if (
            "entity_text" in entity_data
            and entity_data["entity_text"] != current_entity["entity_text"]
        ):
            updates["entity_text"] = entity_data["entity_text"]
            changes["entity_text"] = {
                "old": current_entity["entity_text"],
                "new": entity_data["entity_text"],
            }

            # Regenerate embedding for new text
            updates["embedding"] = await get_text_embedding(entity_data["entity_text"])

        if "properties" in entity_data:
            old_props = current_entity.get("properties", {})
            new_props = entity_data["properties"]

            # Merge properties intelligently
            merged_props = {**old_props, **new_props}
            updates["properties"] = merged_props
            changes["properties"] = {"old": old_props, "new": merged_props}

        if "confidence" in entity_data:
            updates["confidence"] = entity_data["confidence"]
            changes["confidence"] = {
                "old": current_entity.get("confidence"),
                "new": entity_data["confidence"],
            }

        updates["updated_at"] = datetime.now().isoformat()
        updates["updated_by"] = user_id

        # Update PostgreSQL
        await supabase.table("kg_entities").update(updates).eq(
            "id", entity_id
        ).execute()

        # Update Neo4j if neo4j_id exists
        if current_entity.get("neo4j_id"):
            async with neo4j_driver.session() as session:
                update_query = """
                    MATCH (e:Entity) WHERE id(e) = $neo4j_id
                    SET e += $properties
                """
                if "entity_text" in updates:
                    update_query += ", e.entity_text = $entity_text"

                update_query += " RETURN e"

                await session.run(
                    update_query,
                    {
                        "neo4j_id": int(current_entity["neo4j_id"]),
                        "properties": updates.get("properties", {}),
                        "entity_text": updates.get("entity_text"),
                    },
                )

        return {"id": entity_id, "changes": changes}

    async def _delete_entity(self, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Soft delete an entity"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        # Get entity details
        entity_response = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", entity_id)
            .single()
            .execute()
        )
        entity = entity_response.data

        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        # Soft delete in PostgreSQL
        await supabase.table("kg_entities").update(
            {
                "is_active": False,
                "deleted_at": datetime.now().isoformat(),
                "deleted_by": user_id,
                "deleted_reason": "Direct deletion by user",
            }
        ).eq("id", entity_id).execute()

        # Remove from Neo4j
        if entity.get("neo4j_id"):
            async with neo4j_driver.session() as session:
                await session.run(
                    """
                    MATCH (e:Entity) WHERE id(e) = $neo4j_id
                    DETACH DELETE e
                """,
                    {"neo4j_id": int(entity["neo4j_id"])},
                )

        return {"id": entity_id, "deleted": True}

    async def _create_relationship(
        self, relationship_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new relationship"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        # Create relationship in PostgreSQL
        postgres_data = {
            "source_entity_id": relationship_data["source_entity_id"],
            "target_entity_id": relationship_data["target_entity_id"],
            "relationship_type": relationship_data["relationship_type"],
            "properties": relationship_data.get("properties", {}),
            "confidence": relationship_data.get("confidence", 0.8),
            "source_document_id": relationship_data.get("source_document_id"),
            "is_verified": relationship_data.get("is_verified", False),
            "created_by": user_id,
            "is_active": True,
        }

        pg_response = (
            await supabase.table("kg_relationships").insert(postgres_data).execute()
        )
        relationship_id = pg_response.data[0]["id"]

        # Get Neo4j IDs of source and target entities
        source_entity = (
            await supabase.table("kg_entities")
            .select("neo4j_id")
            .eq("id", relationship_data["source_entity_id"])
            .single()
            .execute()
        )
        target_entity = (
            await supabase.table("kg_entities")
            .select("neo4j_id")
            .eq("id", relationship_data["target_entity_id"])
            .single()
            .execute()
        )

        if source_entity.data.get("neo4j_id") and target_entity.data.get("neo4j_id"):
            # Create relationship in Neo4j
            async with neo4j_driver.session() as session:
                neo4j_result = await session.run(
                    """
                    MATCH (source), (target)
                    WHERE id(source) = $source_id AND id(target) = $target_id
                    CREATE (source)-[r:{relationship_type} {{
                        relationship_id: $relationship_id,
                        properties: $properties,
                        created_by: $created_by,
                        created_at: datetime()
                    }}]->(target)
                    RETURN id(r) as neo4j_id
                """.format(
                        relationship_type=relationship_data["relationship_type"]
                    ),
                    {
                        "source_id": int(source_entity.data["neo4j_id"]),
                        "target_id": int(target_entity.data["neo4j_id"]),
                        "relationship_id": relationship_id,
                        "properties": relationship_data.get("properties", {}),
                        "created_by": user_id,
                    },
                )

                record = await neo4j_result.single()
                if record:
                    neo4j_id = record["neo4j_id"]

                    # Update PostgreSQL with Neo4j ID
                    await supabase.table("kg_relationships").update(
                        {"neo4j_id": str(neo4j_id)}
                    ).eq("id", relationship_id).execute()

        return {"id": relationship_id}

    async def rollback_changes(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback applied changes"""

        rollback_actions = rollback_info.get("actions", [])
        rollback_results = []

        # Execute rollback actions in reverse order
        for action in reversed(rollback_actions):
            try:
                if action["type"] == "restore_entity":
                    await self._restore_entity(action["data"])
                elif action["type"] == "delete_entity":
                    await self._delete_entity(action["entity_id"], "system_rollback")
                elif action["type"] == "restore_relationship":
                    await self._restore_relationship(action["data"])
                # Add more rollback action types as needed

                rollback_results.append({"action": action, "status": "success"})

            except Exception as e:
                logger.error(f"Rollback action failed: {e}")
                rollback_results.append(
                    {"action": action, "status": "failed", "error": str(e)}
                )

        return {"rollback_results": rollback_results}

    async def _validate_edit(self, edit: KGEdit) -> List[str]:
        """Validate edit before applying"""

        errors = []

        # Validate entity data
        if edit.entity_data:
            if not edit.entity_data.get("entity_text"):
                errors.append("Entity text is required")
            if not edit.entity_data.get("entity_type"):
                errors.append("Entity type is required")

        # Validate relationship data
        if edit.relationship_data:
            if not edit.relationship_data.get("source_entity_id"):
                errors.append("Source entity ID is required")
            if not edit.relationship_data.get("target_entity_id"):
                errors.append("Target entity ID is required")
            if not edit.relationship_data.get("relationship_type"):
                errors.append("Relationship type is required")

        # Check for circular relationships
        if edit.action == KGEditAction.CREATE_RELATIONSHIP and edit.relationship_data:
            source_id = edit.relationship_data.get("source_entity_id")
            target_id = edit.relationship_data.get("target_entity_id")
            if source_id == target_id:
                errors.append("Cannot create self-referencing relationship")

        return errors

    async def _validate_edit_permissions(
        self, user_id: str, action: KGEditAction
    ) -> bool:
        """Validate user permissions for edit action"""

        from app.api.deps import get_user_permissions

        user_permissions = await get_user_permissions(user_id)

        # Admin has all permissions
        if "admin" in user_permissions.get("roles", []):
            return True

        # Expert can edit entities and relationships
        if "expert" in user_permissions.get("roles", []):
            return action in [
                KGEditAction.CREATE_ENTITY,
                KGEditAction.UPDATE_ENTITY,
                KGEditAction.CREATE_RELATIONSHIP,
                KGEditAction.UPDATE_RELATIONSHIP,
                KGEditAction.MERGE_ENTITIES,
            ]

        # Regular users cannot make direct edits
        return False

    async def _create_rollback_info(self, edit: KGEdit) -> Dict[str, Any]:
        """Create rollback information before applying changes"""

        rollback_actions = []

        if edit.action == KGEditAction.DELETE_ENTITY and edit.entity_data:
            # Store entity data for potential restoration
            supabase = await get_supabase()
            entity_response = (
                await supabase.table("kg_entities")
                .select("*")
                .eq("id", edit.entity_data["id"])
                .single()
                .execute()
            )

            if entity_response.data:
                rollback_actions.append(
                    {"type": "restore_entity", "data": entity_response.data}
                )

        return {"timestamp": datetime.now().isoformat(), "actions": rollback_actions}

    async def _log_change(
        self, edit: KGEdit, user_id: str, applied_changes: List[Dict]
    ) -> None:
        """Log the applied change for audit purposes"""

        supabase = await get_supabase()

        log_entry = {
            "user_id": user_id,
            "action": edit.action.value,
            "reason": edit.reason,
            "applied_changes": applied_changes,
            "timestamp": datetime.now().isoformat(),
        }

        await supabase.table("kg_edit_logs").insert(log_entry).execute()
