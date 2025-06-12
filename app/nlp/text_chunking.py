import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Specialized chunker for Vietnamese text with domain awareness
    """
    
    def __init__(self):
        # Vietnamese sentence endings
        self.sentence_endings = ['.', '!', '?', '。', '！', '？']
        
        # Vietnamese financial document section markers
        self.financial_sections = [
            'thông tin tài khoản', 'thông tin khách hàng', 'lịch sử giao dịch',
            'số dư tài khoản', 'thông tin thẻ', 'khoản vay', 'tiết kiệm',
            'bảo hiểm', 'đầu tư', 'chuyển khoản', 'nạp tiền', 'rút tiền',
            'thanh toán', 'phí dịch vụ', 'lãi suất', 'hạn mức'
        ]
    
    def text_chunk(
        self, 
        text: str, 
        max_tokens: int = 3000, 
        overlap_tokens: int = 300,
        preserve_entities: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Text chunking for Vietnamese financial text
        
        Args:
            text: Vietnamese text to chunk
            max_tokens: Maximum tokens per chunk (roughly 4 chars = 1 token)
            overlap_tokens: Tokens to overlap between chunks
            preserve_entities: Whether to avoid splitting entities
            
        Returns:
            List of chunks with metadata
        """
        max_chars = max_tokens * 4  # Rough conversion
        overlap_chars = overlap_tokens * 4
        
        # First, try to split by financial sections
        section_chunks = self._split_by_financial_sections(text, max_chars)
        
        if len(section_chunks) > 1:
            logger.info(f"Split text into {len(section_chunks)} financial sections")
            return self._add_overlap_to_chunks(section_chunks, overlap_chars)
        
        # If no clear sections, split by paragraphs
        paragraph_chunks = self._split_by_paragraphs(text, max_chars)
        
        if len(paragraph_chunks) > 1:
            logger.info(f"Split text into {len(paragraph_chunks)} paragraph chunks")
            return self._add_overlap_to_chunks(paragraph_chunks, overlap_chars)
        
        # Finally, split by sentences
        sentence_chunks = self._split_by_sentences(text, max_chars)
        
        logger.info(f"Split text into {len(sentence_chunks)} sentence chunks")
        return self._add_overlap_to_chunks(sentence_chunks, overlap_chars)
    
    def _split_by_financial_sections(
        self, 
        text: str, 
        max_chars: int
    ) -> List[Dict[str, Any]]:
        """Split text by Vietnamese financial document sections"""
        chunks = []
        current_chunk = ""
        current_section = "general"
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if line indicates a new financial section
            detected_section = None
            for section in self.financial_sections:
                if section in line_lower:
                    detected_section = section
                    break
            
            # If we found a new section and current chunk is not empty
            if detected_section and current_chunk.strip():
                chunks.append({
                    'text': current_chunk.strip(),
                    'section': current_section,
                    'chunk_type': 'financial_section',
                    'char_count': len(current_chunk),
                    'estimated_tokens': len(current_chunk) // 4
                })
                current_chunk = ""
                current_section = detected_section
            
            current_chunk += line + "\n"
            
            # If chunk is getting too large, split it
            if len(current_chunk) > max_chars:
                chunks.append({
                    'text': current_chunk.strip(),
                    'section': current_section,
                    'chunk_type': 'financial_section',
                    'char_count': len(current_chunk),
                    'estimated_tokens': len(current_chunk) // 4
                })
                current_chunk = ""
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'section': current_section,
                'chunk_type': 'financial_section',
                'char_count': len(current_chunk),
                'estimated_tokens': len(current_chunk) // 4
            })
        
        return chunks
    
    def _split_by_paragraphs(
        self, 
        text: str, 
        max_chars: int
    ) -> List[Dict[str, Any]]:
        """Split text by paragraphs"""
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk + para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': 'paragraph',
                        'chunk_type': 'paragraph',
                        'char_count': len(current_chunk),
                        'estimated_tokens': len(current_chunk) // 4
                    })
                current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'section': 'paragraph',
                'chunk_type': 'paragraph',
                'char_count': len(current_chunk),
                'estimated_tokens': len(current_chunk) // 4
            })
        
        return chunks
    
    def _split_by_sentences(
        self, 
        text: str, 
        max_chars: int
    ) -> List[Dict[str, Any]]:
        """Split text by Vietnamese sentences"""
        # Vietnamese sentence splitting regex
        sentence_pattern = r'[.!?。！？]+(?:\s|$)'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk + sentence) < max_chars:
                current_chunk += sentence + ". "
            else:
                if current_chunk.strip():
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': 'sentence',
                        'chunk_type': 'sentence',
                        'char_count': len(current_chunk),
                        'estimated_tokens': len(current_chunk) // 4
                    })
                current_chunk = sentence + ". "
        
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'section': 'sentence',
                'chunk_type': 'sentence',
                'char_count': len(current_chunk),
                'estimated_tokens': len(current_chunk) // 4
            })
        
        return chunks
    
    def _add_overlap_to_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        overlap_chars: int
    ) -> List[Dict[str, Any]]:
        """Add overlapping context between chunks"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            text = chunk['text']
            
            # Add overlap from previous chunk
            if i > 0 and overlap_chars > 0:
                prev_text = chunks[i-1]['text']
                if len(prev_text) > overlap_chars:
                    overlap_start = prev_text[-overlap_chars:]
                    # Find a good break point (sentence ending)
                    for ending in self.sentence_endings:
                        last_ending = overlap_start.rfind(ending)
                        if last_ending > overlap_chars // 2:
                            overlap_start = overlap_start[last_ending+1:].strip()
                            break
                    text = overlap_start + " " + text
            
            # Add overlap to next chunk
            if i < len(chunks) - 1 and overlap_chars > 0:
                next_text = chunks[i+1]['text']
                if len(next_text) > overlap_chars:
                    overlap_end = next_text[:overlap_chars]
                    # Find a good break point
                    for ending in self.sentence_endings:
                        first_ending = overlap_end.find(ending)
                        if first_ending > overlap_chars // 2:
                            overlap_end = overlap_end[:first_ending+1].strip()
                            break
                    text = text + " " + overlap_end
            
            overlapped_chunk = chunk.copy()
            overlapped_chunk['text'] = text
            overlapped_chunk['has_overlap'] = i > 0 or i < len(chunks) - 1
            overlapped_chunk['original_char_count'] = chunk['char_count']
            overlapped_chunk['char_count'] = len(text)
            overlapped_chunk['estimated_tokens'] = len(text) // 4
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks


