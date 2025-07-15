import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.tasks.executors.graph_state import GraphDataType

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class TextChunkingExecutor(BaseStepExecutor):
    """Executor for text chunking với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Text chunking cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for chunking")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.nlp.text_chunking import TextChunker
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger
            from app.tasks.kg_extraction import KgExtractionTask

            step_service = PipelineStepService()

            self.logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            text_chunker = TextChunker()
            chunk_size = self.config.get("chunk_size", 1000)
            chunk_overlap = self.config.get("chunk_overlap", 200)
            chunking_strategy = self.config.get("chunking_strategy", "recursive")

            # Get text data từ graph state
            text_data = self._get_best_text_data()

            chunked_data = []

            for text_item in text_data:
                text_content: str = text_item.get("text", "") or text_item.get(
                    "content", ""
                )

                if chunking_strategy == "structured":
                    if isinstance(text_content, (dict, list)):
                        chunks = text_chunker.text_chunk(text_content, chunk_size)
                    else:
                        chunks = text_chunker.text_chunk(
                            text_content, chunk_size, chunk_overlap
                        )
                else:
                    chunks = text_chunker.text_chunk(
                        text_content, chunk_size, chunk_overlap
                    )

                await self.logger.info(
                    f"Chunking text from source '{text_item.get('source', 'unknown')}' "
                    f"into {len(chunks)} chunks with size {chunk_size} and overlap {chunk_overlap}"
                )

                for i, chunk in enumerate(chunks):
                    chunked_item = {
                        "chunk_id": f"{text_item.get('source', 'unknown')}_{i}",
                        "content": (
                            chunk.get("text", chunk)
                            if isinstance(chunk, dict)
                            else chunk
                        ),
                        "section": (
                            chunk.get("section", "unknown")
                            if isinstance(chunk, dict)
                            else "unknown"
                        ),
                        "chunk_type": (
                            chunk.get("chunk_type", "text")
                            if isinstance(chunk, dict)
                            else "text"
                        ),
                        "char_count": chunk.get("char_count", len(str(chunk))),
                        "estimated_tokens": chunk.get("estimated_tokens", 0),
                        "chunk_index": i,
                        "source": text_item.get("source"),
                        "original_provenance": text_item.get("provenance", {}),
                    }
                    chunked_data.append(self._track_provenance(chunked_item))

            return {
                "chunks": chunked_data,
                "total_chunks": len(chunked_data),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "text_chunking",
                    "chunking_strategy": chunking_strategy,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Text chunking execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với processed chunks"""
        if "chunks" in step_result:
            chunk_data = []
            for chunk_item in step_result["chunks"]:
                if isinstance(chunk_item, dict) and "data" in chunk_item:
                    chunk_data.append(chunk_item["data"])

            if chunk_data:
                self.graph_state.set_text_data(
                    chunk_data, GraphDataType.PROCESSED_CHUNKS, self.step_name
                )
