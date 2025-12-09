"""Text processing utilities for chunking and preprocessing."""
from typing import List, Dict, Any, Optional
import re
import hashlib
import structlog

from config import settings

logger = structlog.get_logger()


class TextChunker:
    """Utility for splitting text into chunks for embedding."""

    def __init__(
            self,
            chunk_size: int = None,
            chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

    def chunk_text(
            self,
            text: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks with metadata.

        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunks with text and metadata
        """
        if not text:
            return []

        # Clean the text
        text = self._clean_text(text)

        # Split into sentences for better chunking
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If single sentence is larger than chunk size, split it
            if sentence_size > self.chunk_size:
                # Add current chunk if it exists
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))
                    # Keep overlap
                    overlap_text = chunk_text[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                    current_chunk = [overlap_text] if overlap_text else []
                    current_size = len(overlap_text)

                # Split large sentence
                words = sentence.split()
                for i in range(0, len(words), self.chunk_size // 4):  # Approximate word chunking
                    word_chunk = " ".join(words[i:i + self.chunk_size // 4])
                    chunks.append(self._create_chunk(word_chunk, metadata, len(chunks)))

                current_chunk = []
                current_size = 0
                continue

            # Check if adding sentence exceeds chunk size
            if current_size + sentence_size + 1 > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))

                    # Keep overlap for next chunk
                    if self.chunk_overlap > 0:
                        overlap_text = chunk_text[-self.chunk_overlap:]
                        current_chunk = [overlap_text]
                        current_size = len(overlap_text)
                    else:
                        current_chunk = []
                        current_size = 0

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size + 1

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))

        logger.info(f"Created {len(chunks)} chunks from text", text_length=len(text))
        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text by removing extra whitespace and special characters."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be enhanced with nltk or spacy)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Remove empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    @staticmethod
    def _create_chunk(
            text: str,
            metadata: Optional[Dict[str, Any]],
            index: int
    ) -> Dict[str, Any]:
        """Create a chunk dictionary with text and metadata."""
        chunk_id = hashlib.md5(f"{text}_{index}".encode()).hexdigest()

        chunk: dict[str, Any] = {
            "text": text,
            "chunk_id": chunk_id,
            "index": index,
            "char_count": len(text),
            "word_count": len(text.split())
        }

        if metadata:
            chunk["metadata"] = metadata

        return chunk


class TextPreprocessor:
    """Preprocess text for better embedding and retrieval."""

    @staticmethod
    def preprocess_for_embedding(text: str) -> str:
        """Preprocess text before generating embeddings."""
        # Convert to lowercase for consistency
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction (can be enhanced with NLP libraries)
        # Remove common stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are',
            'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'shall', 'to', 'of', 'in', 'for',
            'with', 'by', 'from', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'up', 'down', 'out',
            'off', 'over', 'under', 'again', 'further', 'then', 'once'
        }

        # Tokenize and filter
        words = text.lower().split()
        keywords = []

        for word in words:
            # Clean word
            word = re.sub(r'[^\w\s]', '', word)
            # Check if not stop word and has meaningful length
            if word and word not in stop_words and len(word) > 2:
                keywords.append(word)

        # Return unique keywords
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:max_keywords]


# Global instances
text_chunker = TextChunker()
text_preprocessor = TextPreprocessor()
