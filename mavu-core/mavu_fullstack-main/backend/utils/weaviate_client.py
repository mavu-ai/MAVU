"""Weaviate client and collection management."""
import asyncio

from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import structlog
import weaviate

from weaviate.classes.config import Configure, Property, DataType

from config import settings

logger = structlog.get_logger()


class WeaviateClient:
    """Weaviate client for vector database operations."""

    def __init__(self):
        self.client = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Initialize connection to Weaviate."""
        async with self._lock:
            if self.client is not None:
                return

            try:
                # Use the v4 WeaviateClient for connections
                import weaviate.classes as wvc

                if settings.weaviate_api_key and settings.weaviate_api_key != "optional_api_key":
                    # Cloud connection with API key
                    self.client = weaviate.WeaviateClient(
                        connection_params=wvc.init.ConnectionParams(
                            http=wvc.init.Protocols(
                                host=settings.weaviate_url.replace("http://", "").replace("https://", ""),
                                secure=False
                            )
                        ),
                        auth_client_secret=weaviate.auth.AuthApiKey(settings.weaviate_api_key)
                    )
                else:
                    # Local connection without authentication
                    # Parse host and port from WEAVIATE_URL environment variable
                    import re
                    url_match = re.match(r'https?://([^:]+):?(\d+)?', settings.weaviate_url)
                    if url_match:
                        host = url_match.group(1)
                        port = int(url_match.group(2)) if url_match.group(2) else 8080
                    else:
                        host = "localhost"
                        port = 8080

                    # Connect with skip_init_checks and proper gRPC port
                    self.client = weaviate.connect_to_local(
                        host=host,
                        port=port,
                        grpc_port=50051,  # Default gRPC port
                        skip_init_checks=True
                    )

                await self._setup_collections()
                logger.info("Successfully connected to Weaviate", url=settings.weaviate_url)
            except Exception as e:
                logger.error("Failed to connect to Weaviate", error=str(e))
                raise

    async def _setup_collections(self):
        """Create collections if they don't exist."""
        try:
            # Create UserContext collection
            if not self.client.collections.exists("UserContext"):
                try:
                    self.client.collections.create(
                        name="UserContext",
                        vectorizer_config=Configure.Vectorizer.none(),
                        properties=[
                            Property(name="owner_id", data_type=DataType.TEXT),
                            Property(name="text_chunk", data_type=DataType.TEXT),
                            Property(name="metadata", data_type=DataType.TEXT),
                            # Changed from OBJECT to TEXT for JSON storage
                            Property(name="created_at", data_type=DataType.DATE),
                            Property(name="source", data_type=DataType.TEXT),
                        ]
                    )
                    logger.info("Created UserContext collection")
                except Exception as create_error:
                    if "already exists" in str(create_error):
                        logger.info("UserContext collection already exists, skipping creation")
                    else:
                        raise

            # Create AppContext collection
            if not self.client.collections.exists("AppContext"):
                try:
                    self.client.collections.create(
                        name="AppContext",
                        vectorizer_config=Configure.Vectorizer.none(),
                        properties=[
                            Property(name="text_chunk", data_type=DataType.TEXT),
                            Property(name="metadata", data_type=DataType.TEXT),
                            # Changed from OBJECT to TEXT for JSON storage
                            Property(name="created_at", data_type=DataType.DATE),
                            Property(name="source", data_type=DataType.TEXT),
                            Property(name="category", data_type=DataType.TEXT),
                        ]
                    )
                    logger.info("Created AppContext collection")
                except Exception as create_error:
                    if "already exists" in str(create_error):
                        logger.info("AppContext collection already exists, skipping creation")
                    else:
                        raise

        except Exception as e:
            logger.error("Failed to setup collections", error=str(e))
            raise

    async def disconnect(self):
        """Close connection to Weaviate."""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Disconnected from Weaviate")

    async def store_user_context(
            self,
            owner_id: str,
            text_chunk: str,
            embedding: List[float],
            metadata: Dict[str, Any],
            source: str = "user_upload"
    ) -> str:
        """Store user-specific context in Weaviate."""
        try:
            from datetime import datetime, timezone
            import json

            collection = self.client.collections.get("UserContext")
            result = await asyncio.to_thread(
                collection.data.insert,
                properties={
                    "owner_id": owner_id,
                    "text_chunk": text_chunk,
                    "metadata": json.dumps(metadata),  # Convert dict to JSON string
                    "source": source,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                vector=embedding
            )
            logger.info("Stored user context", owner_id=owner_id, chunk_id=str(result))
            return str(result)
        except Exception as e:
            logger.error("Failed to store user context", error=str(e))
            raise

    async def store_app_context(
            self,
            text_chunk: str,
            embedding: List[float],
            metadata: Dict[str, Any],
            source: str = "app_upload",
            category: str = "general"
    ) -> str:
        """Store application-wide context in Weaviate."""
        try:
            from datetime import datetime, timezone
            import json

            collection = self.client.collections.get("AppContext")
            result = await asyncio.to_thread(
                collection.data.insert,
                properties={
                    "text_chunk": text_chunk,
                    "metadata": json.dumps(metadata),  # Convert dict to JSON string
                    "source": source,
                    "category": category,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                vector=embedding
            )
            logger.info("Stored app context", chunk_id=str(result))
            return str(result)
        except Exception as e:
            logger.error("Failed to store app context", error=str(e))
            raise

    async def search_user_context(
            self,
            owner_id: str,
            query_embedding: List[float],
            limit: int = 5,
            certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search user-specific context."""
        try:
            collection = self.client.collections.get("UserContext")
            # Get more results for filtering since we need to filter by owner_id
            response = await asyncio.to_thread(
                collection.query.near_vector,
                near_vector=query_embedding,
                limit=limit * 3,  # Get more results to ensure enough after filtering
                return_properties=["text_chunk", "metadata", "source", "owner_id"],
                return_metadata=["distance", "certainty"]
            )

            # Filter results by owner_id manually
            import json
            results = []
            for item in response.objects:
                if item.properties.get("owner_id") == owner_id:
                    metadata = item.properties.get("metadata")
                    # Parse JSON string back to dict if needed
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            pass
                    results.append({
                        "text": item.properties.get("text_chunk"),
                        "metadata": metadata,
                        "source": item.properties.get("source"),
                        "distance": item.metadata.distance,
                        "certainty": item.metadata.certainty
                    })
                    if len(results) >= limit:
                        break

            logger.info(f"Found {len(results)} user context matches", owner_id=owner_id)
            return results
        except Exception as e:
            logger.error("Failed to search user context", error=str(e))
            return []

    async def search_app_context(
            self,
            query_embedding: List[float],
            limit: int = 5,
            certainty: float = 0.7,
            category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search application-wide context."""
        try:
            collection = self.client.collections.get("AppContext")

            # Get more results if we need to filter by category
            query_limit = limit * 2 if category else limit

            response = await asyncio.to_thread(
                collection.query.near_vector,
                near_vector=query_embedding,
                limit=query_limit,
                return_properties=["text_chunk", "metadata", "source", "category"],
                return_metadata=["distance", "certainty"]
            )

            # Filter by category manually if specified
            import json
            results = []
            for item in response.objects:
                if category and item.properties.get("category") != category:
                    continue

                metadata = item.properties.get("metadata")
                # Parse JSON string back to dict if needed
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass

                results.append({
                    "text": item.properties.get("text_chunk"),
                    "metadata": metadata,
                    "source": item.properties.get("source"),
                    "category": item.properties.get("category"),
                    "distance": item.metadata.distance,
                    "certainty": item.metadata.certainty
                })

                if len(results) >= limit:
                    break

            logger.info(f"Found {len(results)} app context matches")
            return results
        except Exception as e:
            logger.error("Failed to search app context", error=str(e))
            return []

    async def hybrid_search(
            self,
            owner_id: str,
            query_text: str,
            query_embedding: List[float],
            limit: int = 5,
            alpha: float = 0.5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform hybrid search combining vector and keyword search."""
        try:
            user_collection = self.client.collections.get("UserContext")
            app_collection = self.client.collections.get("AppContext")

            # Hybrid search for user context
            # Note: Weaviate v4 hybrid search doesn't support where filter directly
            # We need to do post-filtering or use a different approach
            user_response = await asyncio.to_thread(
                user_collection.query.hybrid,
                query=query_text,
                vector=query_embedding,
                alpha=alpha,
                limit=limit * 2,  # Get more results for filtering
                return_properties=["text_chunk", "metadata", "source", "owner_id"],
                return_metadata=["distance", "score"]
            )

            # Filter results by owner_id manually
            filtered_user_objects = [
                obj for obj in user_response.objects
                if obj.properties.get("owner_id") == owner_id
            ][:limit]

            # Hybrid search for app context
            app_response = await asyncio.to_thread(
                app_collection.query.hybrid,
                query=query_text,
                vector=query_embedding,
                alpha=alpha,
                limit=limit,
                return_properties=["text_chunk", "metadata", "source", "category"],
                return_metadata=["distance", "score"]
            )

            import json
            user_results = []
            for item in filtered_user_objects:
                metadata = item.properties.get("metadata")
                # Parse JSON string back to dict if needed
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                user_results.append({
                    "text": item.properties.get("text_chunk"),
                    "metadata": metadata,
                    "source": item.properties.get("source"),
                    "score": item.metadata.score if hasattr(item.metadata, 'score') else 0
                })

            app_results = []
            for item in app_response.objects:
                metadata = item.properties.get("metadata")
                # Parse JSON string back to dict if needed
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        pass
                app_results.append({
                    "text": item.properties.get("text_chunk"),
                    "metadata": metadata,
                    "source": item.properties.get("source"),
                    "category": item.properties.get("category"),
                    "score": item.metadata.score
                })

            logger.info(
                f"Hybrid search complete",
                user_matches=len(user_results),
                app_matches=len(app_results)
            )

            return {
                "user_context": user_results,
                "app_context": app_results
            }
        except Exception as e:
            logger.error("Failed to perform hybrid search", error=str(e))
            # Fallback to vector search if hybrid fails (gRPC issues)
            logger.info("Falling back to vector search")
            try:
                user_results_fallback = await self.search_user_context(owner_id, query_embedding, limit)
                app_results_fallback = await self.search_app_context(query_embedding, limit)
                return {
                    "user_context": user_results_fallback,
                    "app_context": app_results_fallback
                }
            except Exception as fallback_error:
                logger.error("Fallback vector search also failed", error=str(fallback_error))
                return {"user_context": [], "app_context": []}


# Global client instance
weaviate_client = WeaviateClient()


@asynccontextmanager
async def get_weaviate_client():
    """Get connected Weaviate client."""
    if weaviate_client.client is None:
        await weaviate_client.connect()
    yield weaviate_client
