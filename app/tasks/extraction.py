import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import os
from datetime import datetime

from app.core.supabase import get_supabase
from app.utils.s3 import download_file_from_s3
from app.utils.file_handler import get_file_type, parse_file_content
from app.nlp.entity_extraction import extract_entities
from app.nlp.relation_extraction import extract_relationships
from app.nlp.text_chunking import chunk_text

logger = logging.getLogger(__name__)

async def process_file(file_id: UUID) -> bool:
    """
    Process a file to extract entities and relationships.
    
    Args:
        file_id: ID of the file to process
        
    Returns:
        True if processing was successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # Get file information
        response = await supabase.table("file_uploads").select("*").eq("id", str(file_id)).execute()
        
        if not response.data:
            logger.error(f"File {file_id} not found")
            return False
        
        file_info = response.data[0]
        
        # Update status to processing
        await supabase.table("file_uploads").update({
            "upload_status": "processing"
        }).eq("id", str(file_id)).execute()
        
        # Download file from S3
        storage_path = file_info["storage_path"]
        local_path = await download_file_from_s3(storage_path)
        
        if not local_path or not os.path.exists(local_path):
            logger.error(f"Failed to download file from S3: {storage_path}")
            await supabase.table("file_uploads").update({
                "upload_status": "failed",
                "metadata": {
                    **(file_info.get("metadata") or {}),
                    "error": "Failed to download file from S3"
                }
            }).eq("id", str(file_id)).execute()
            return False
        
        # Determine file type and parse content
        file_type = get_file_type(file_info["file_name"], file_info["file_type"])
        text_content = await parse_file_content(local_path, file_type)
        
        if not text_content:
            logger.error(f"Failed to parse file content: {local_path}")
            await supabase.table("file_uploads").update({
                "upload_status": "failed",
                "metadata": {
                    **(file_info.get("metadata") or {}),
                    "error": "Failed to parse file content"
                }
            }).eq("id", str(file_id)).execute()
            return False
        
        # Process the text in chunks
        chunks = chunk_text(text_content)
        
        total_entities = 0
        total_relationships = 0
        
        for i, chunk in enumerate(chunks):
            # Extract entities
            entities = await extract_entities(chunk)
            
            # Log progress
            logger.info(f"Extracted {len(entities)} entities from chunk {i+1}/{len(chunks)}")
            
            # Extract relationships
            relationships = await extract_relationships(chunk, entities)
            
            # Log progress
            logger.info(f"Extracted {len(relationships)} relationships from chunk {i+1}/{len(chunks)}")
            
            # Save extraction results
            await save_extraction_results(
                file_id=file_id,
                chunk_index=i,
                text_length=len(chunk),
                entities=entities,
                relationships=relationships
            )
            
            total_entities += len(entities)
            total_relationships += len(relationships)
        
        # Update file status to completed
        await supabase.table("file_uploads").update({
            "upload_status": "completed",
            "processed": True,
            "metadata": {
                **(file_info.get("metadata") or {}),
                "total_entities": total_entities,
                "total_relationships": total_relationships,
                "chunks_processed": len(chunks),
                "processed_at": datetime.utcnow().isoformat()
            }
        }).eq("id", str(file_id)).execute()
        
        # Clean up local file
        if os.path.exists(local_path):
            os.remove(local_path)
        
        logger.info(f"Successfully processed file {file_id}: {total_entities} entities, {total_relationships} relationships")
        return True
    
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {str(e)}")
        
        # Update file status to failed
        try:
            supabase = get_supabase()
            response = await supabase.table("file_uploads").select("metadata").eq("id", str(file_id)).execute()
            
            if response.data:
                metadata = response.data[0].get("metadata") or {}
                await supabase.table("file_uploads").update({
                    "upload_status": "failed",
                    "metadata": {
                        **metadata,
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat()
                    }
                }).eq("id", str(file_id)).execute()
        except Exception as update_error:
            logger.error(f"Error updating file status for {file_id}: {str(update_error)}")
        
        return False

async def save_extraction_results(
    file_id: UUID,
    chunk_index: int,
    text_length: int,
    entities: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]]
) -> bool:
    """
    Save extraction results to the database.
    
    Args:
        file_id: ID of the file being processed
        chunk_index: Index of the text chunk
        text_length: Length of the text chunk
        entities: Extracted entities
        relationships: Extracted relationships
        
    Returns:
        True if saving was successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # Create extraction result record
        extraction_result = {
            "pipeline_run_id": None,  # No pipeline run for direct file processing
            "source_id": str(file_id),
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "processed_text_length": text_length,
            "extracted_entities": entities,
            "extracted_relationships": relationships,
            "status": "completed",
            "error_message": None,
            "metadata": {
                "chunk_index": chunk_index
            }
        }
        
        # Insert into database
        await supabase.table("extraction_results").insert(extraction_result).execute()
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving extraction results for file {file_id}, chunk {chunk_index}: {str(e)}")
        return False

async def sync_extraction_results_to_graph(extraction_result_id: UUID) -> bool:
    """
    Sync extraction results to the knowledge graph.
    
    Args:
        extraction_result_id: ID of the extraction result to sync
        
    Returns:
        True if syncing was successful, False otherwise
    """
    try:
        supabase = get_supabase()
        
        # Get extraction result
        response = await supabase.table("extraction_results").select("*").eq("id", str(extraction_result_id)).execute()
        
        if not response.data:
            logger.error(f"Extraction result {extraction_result_id} not found")
            return False
        
        extraction_result = response.data[0]
        entities = extraction_result.get("extracted_entities") or []
        relationships = extraction_result.get("extracted_relationships") or []
        source_id = extraction_result.get("source_id")
        
        # Create entities in database and Neo4j
        entity_mapping = {}  # Map from entity text to entity ID
        
        for entity in entities:
            # Check if entity already exists
            existing_response = await supabase.table("kg_entities").select("id").eq("entity_text", entity["entity_text"]).eq("entity_type", entity["entity_type"]).execute()
            
            if existing_response.data:
                # Entity exists, use existing ID
                entity_id = existing_response.data[0]["id"]
                entity_mapping[entity["entity_text"]] = entity_id
            else:
                # Create new entity
                entity_data = {
                    "entity_text": entity["entity_text"],
                    "entity_type": entity["entity_type"],
                    "source_document_id": source_id,
                    "properties": entity.get("properties", {}),
                    "confidence": entity.get("confidence", 0.8),
                    "is_verified": False
                }
                
                create_response = await supabase.table("kg_entities").insert(entity_data).execute()
                
                if create_response.data:
                    entity_id = create_response.data[0]["id"]
                    entity_mapping[entity["entity_text"]] = entity_id
        
        # Create relationships
        for relationship in relationships:
            source_text = relationship["source_entity"]
            target_text = relationship["target_entity"]
            
            if source_text in entity_mapping and target_text in entity_mapping:
                source_id = entity_mapping[source_text]
                target_id = entity_mapping[target_text]
                
                relationship_data = {
                    "source_entity_id": source_id,
                    "target_entity_id": target_id,
                    "relationship_type": relationship["relationship_type"],
                    "source_document_id": extraction_result["source_id"],
                    "properties": relationship.get("properties", {}),
                    "confidence": relationship.get("confidence", 0.7),
                    "is_verified": False
                }
                
                await supabase.table("kg_relationships").insert(relationship_data).execute()
        
        # Update extraction result status
        await supabase.table("extraction_results").update({
            "synced_to_graph": True,
            "synced_at": datetime.utcnow().isoformat()
        }).eq("id", str(extraction_result_id)).execute()
        
        return True
    
    except Exception as e:
        logger.error(f"Error syncing extraction result {extraction_result_id} to graph: {str(e)}")
        return False
