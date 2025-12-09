"""RAG (Retrieval-Augmented Generation) pipeline."""
import asyncio
from typing import Any, Dict, Optional
import structlog
import hashlib
from datetime import datetime

from utils.weaviate_client import weaviate_client
from utils.embeddings import embedding_service, QuotaExceededError
from utils.text_processing import text_chunker
from config import settings

logger = structlog.get_logger()


class RAGPipeline:
    """Complete RAG pipeline for context retrieval and augmentation."""

    def __init__(self):
        self.cache = {}  # Simple in-memory cache (can be replaced with Redis)
        self.cache_ttl = settings.redis_cache_ttl

    async def retrieve_context(
        self,
        query: str,
        owner_id: str,
        use_hybrid: bool = True,
        top_k_user: Optional[int] = None,
        top_k_app: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context from both user and app collections.

        Args:
            query: The search query
            owner_id: User ID for filtering user context
            use_hybrid: Whether to use hybrid search (vector + keyword)
            top_k_user: Number of user context results (default from settings)
            top_k_app: Number of app context results (default from settings)

        Returns:
            Dictionary with user_context and app_context results
        """
        try:
            # Check cache
            cache_key = self._generate_cache_key(query, owner_id, use_hybrid)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("Retrieved context from cache")
                return cached_result

            # Generate query embedding with quota handling
            try:
                query_embedding = await embedding_service.generate_query_embedding(query)
            except QuotaExceededError:
                logger.warning(
                    "OpenAI quota exceeded - continuing without RAG context",
                    user_message="Voice chat will continue without personalized context"
                )
                return {
                    "user_context": [],
                    "app_context": [],
                    "quota_exceeded": True,
                    "message": "Continuing without personalized context (quota exceeded)"
                }

            # Handle None embedding (quota exceeded without exception)
            if query_embedding is None:
                logger.warning("Embedding generation returned None - quota likely exceeded")
                return {
                    "user_context": [],
                    "app_context": [],
                    "quota_exceeded": True,
                    "message": "Continuing without personalized context"
                }

            top_k_user = top_k_user or settings.rag_top_k_user
            top_k_app = top_k_app or settings.rag_top_k_app

            if use_hybrid:
                # Hybrid search (vector + keyword)
                results = await weaviate_client.hybrid_search(
                    owner_id=owner_id,
                    query_text=query,
                    query_embedding=query_embedding,
                    limit=max(top_k_user, top_k_app)
                )
                # Limit results to specified top_k
                results["user_context"] = results["user_context"][:top_k_user]
                results["app_context"] = results["app_context"][:top_k_app]
            else:
                # Pure vector search
                user_task = weaviate_client.search_user_context(
                    owner_id=owner_id,
                    query_embedding=query_embedding,
                    limit=top_k_user
                )
                app_task = weaviate_client.search_app_context(
                    query_embedding=query_embedding,
                    limit=top_k_app
                )
                user_results, app_results = await asyncio.gather(user_task, app_task)

                results = {
                    "user_context": user_results,
                    "app_context": app_results
                }

            # Add metadata
            results["query"] = query
            results["timestamp"] = datetime.now().isoformat()
            results["retrieval_method"] = "hybrid" if use_hybrid else "vector"

            # Cache results
            self._add_to_cache(cache_key, results)

            logger.info(
                "Retrieved context",
                user_matches=len(results["user_context"]),
                app_matches=len(results["app_context"])
            )

            return results

        except QuotaExceededError:
            # Graceful degradation - continue without RAG
            logger.warning("Quota exceeded - operating without RAG context")
            return {
                "user_context": [],
                "app_context": [],
                "quota_exceeded": True,
                "message": "Continuing without personalized context"
            }
        except Exception as e:
            logger.error("Failed to retrieve context", error=str(e), error_type=type(e).__name__)
            # Graceful degradation - return empty context instead of crashing
            return {
                "user_context": [],
                "app_context": [],
                "error": str(e),
                "message": "Continuing without context due to error"
            }

    @staticmethod
    async def augment_prompt(
        base_prompt: str,
        context: Dict[str, Any],
        max_context_length: int = 2000
    ) -> str:
        """
        Augment the base prompt with retrieved context.

        Args:
            base_prompt: The original user prompt
            context: Retrieved context from RAG
            max_context_length: Maximum length of context to include

        Returns:
            Augmented prompt with context
        """
        try:
            # Format user context
            user_context_str = ""
            if context.get("user_context"):
                user_chunks = [
                    f"- {item['text']}"
                    for item in context["user_context"]
                    if item.get("text")
                ]
                if user_chunks:
                    user_context_str = "Your Personal Context:\n" + "\n".join(user_chunks)

            # Format app context
            app_context_str = ""
            if context.get("app_context"):
                app_chunks = [
                    f"- {item['text']}"
                    for item in context["app_context"]
                    if item.get("text")
                ]
                if app_chunks:
                    app_context_str = "Application Knowledge:\n" + "\n".join(app_chunks)

            # Combine contexts
            full_context = []
            if user_context_str:
                full_context.append(user_context_str)
            if app_context_str:
                full_context.append(app_context_str)

            if not full_context:
                return base_prompt

            # Truncate if necessary
            context_text = "\n\n".join(full_context)
            if len(context_text) > max_context_length:
                context_text = context_text[:max_context_length] + "..."

            # Create augmented prompt
            augmented_prompt = f"""<context>
{context_text}
</context>

Based on the above context, please respond to the following:
{base_prompt}"""

            return augmented_prompt

        except Exception as e:
            logger.error("Failed to augment prompt", error=str(e))
            return base_prompt

    @staticmethod
    async def process_and_store_document(
        document_text: str,
        owner_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "upload",
        is_app_context: bool = False
    ) -> Dict[str, Any]:
        """
        Process a document and store it in Weaviate.

        Args:
            document_text: The document text to process
            owner_id: User ID (required if not app context)
            metadata: Additional metadata for the document
            source: Source identifier for the document
            is_app_context: Whether this is app-wide context

        Returns:
            Processing result with chunk IDs
        """
        try:
            # Chunk the document
            chunks = text_chunker.chunk_text(document_text, metadata)

            if not chunks:
                return {
                    "success": False,
                    "error": "No chunks created from document"
                }

            # Generate embeddings for all chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)

            # Store chunks in Weaviate
            stored_ids = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk_metadata = {
                    **(metadata or {}),
                    "chunk_index": chunk["index"],
                    "chunk_id": chunk["chunk_id"],
                    "word_count": chunk["word_count"],
                    "char_count": chunk["char_count"]
                }

                if is_app_context:
                    chunk_id = await weaviate_client.store_app_context(
                        text_chunk=chunk["text"],
                        embedding=embedding,
                        metadata=chunk_metadata,
                        source=source
                    )
                else:
                    if not owner_id:
                        raise ValueError("owner_id is required for user context")

                    chunk_id = await weaviate_client.store_user_context(
                        owner_id=owner_id,
                        text_chunk=chunk["text"],
                        embedding=embedding,
                        metadata=chunk_metadata,
                        source=source
                    )

                stored_ids.append(chunk_id)

            logger.info(
                f"Stored {len(stored_ids)} chunks",
                is_app_context=is_app_context,
                owner_id=owner_id
            )

            return {
                "success": True,
                "chunks_created": len(stored_ids),
                "chunk_ids": stored_ids,
                "total_chars": sum(c["char_count"] for c in chunks),
                "total_words": sum(c["word_count"] for c in chunks)
            }

        except Exception as e:
            logger.error("Failed to process document", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def _generate_cache_key(
        query: str,
        owner_id: str,
        use_hybrid: bool
    ) -> str:
        """Generate a cache key for the query."""
        key_data = f"{query}_{owner_id}_{use_hybrid}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache if exists and not expired."""
        if key in self.cache:
            cached_item = self.cache[key]
            # Simple TTL check (should use Redis in production)
            if cached_item.get("timestamp"):
                # For now, just return cached item
                return cached_item.get("data")
        return None

    def _add_to_cache(self, key: str, data: Dict[str, Any]):
        """Add result to cache."""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        # In production, implement cache eviction strategy


class RAGContextManager:
    """Manage RAG context for streaming responses."""

    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline
        self.current_context = None
        self.context_history = []

    async def prepare_context(
        self,
        query: str,
        owner_id: str,
        system_instructions: str = ""
    ) -> str:
        """
        Prepare context-augmented instructions for the model.

        Args:
            query: User query
            owner_id: User ID
            system_instructions: Base system instructions

        Returns:
            Augmented system instructions
        """
        # Retrieve context
        context = await self.pipeline.retrieve_context(
            query=query,
            owner_id=owner_id
        )

        self.current_context = context
        self.context_history.append({
            "query": query,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })

        # Format context for system prompt
        context_parts = []

        # Add user context
        if context.get("user_context"):
            user_info = "\n".join([
                f"- {item['text']}"
                for item in context["user_context"][:3]  # Top 3 most relevant
            ])
            context_parts.append(f"User Context:\n{user_info}")

        # Add app context
        if context.get("app_context"):
            app_info = "\n".join([
                f"- {item['text']}"
                for item in context["app_context"][:3]  # Top 3 most relevant
            ])
            context_parts.append(f"Application Knowledge:\n{app_info}")

        # Combine with system instructions
        if context_parts:
            augmented_instructions = f"""{system_instructions}

<context>
{chr(10).join(context_parts)}
</context>

Use the above context to provide personalized and informed responses. Reference specific information from the context when relevant."""
        else:
            augmented_instructions = system_instructions

        return augmented_instructions

    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get the current context."""
        return self.current_context

    def clear_context(self):
        """Clear current context."""
        self.current_context = None


# Global pipeline instance
rag_pipeline = RAGPipeline()