import logging
from uuid import UUID

from app.core.supabase import get_supabase
from app.nlp.entity_extraction import EntityExtractionService
from app.nlp.relation_extraction import RelationshipExtractionService
from app.utils.file_handler import get_file_type
from app.utils.file_processor import FileProcessor

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
        from app.services.file_upload import UploadService

        supabase = await get_supabase()
        upload_service = UploadService()
        file_processor = FileProcessor()

        # Get file information
        response = (
            await supabase.table("file_uploads")
            .select("*")
            .eq("id", str(file_id))
            .execute()
        )

        if not response.data:
            logger.error(f"File {file_id} not found")
            return False

        file_info = response.data[0]

        file_content = await upload_service.get_file_content(file_upload_id=file_id)

        if not file_content:
            logger.error(f"File content for {file_id} is empty or not found")
            return False

        temp_file_path = f"/tmp/{file_info["id"]}.{file_info["file_name"]}"
        # Save to temporary file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)

        file_path = temp_file_path
        file_type = get_file_type(file_path)
        if not file_type:
            logger.error(f"Unsupported file type for {file_path}")
            return False

        if file_processor.is_structured_file(file_type):
            logger.info(f"Processing structured file: {file_path}")
            await file_processor.process_structured_file(file_path, file_type)
        elif file_processor.is_unstructured_file(file_type):
            logger.info(f"Processing unstructured file: {file_path}")
            await file_processor.process_unstructured_file(file_path, file_type)

        return True
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {e}")
        return False
