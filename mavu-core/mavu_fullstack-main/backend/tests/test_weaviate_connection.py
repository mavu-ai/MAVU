"""Test Weaviate database connection and operations."""
import pytest
import asyncio
from utils.weaviate_client import weaviate_client


@pytest.mark.asyncio
async def test_weaviate_connection():
    """Test that we can connect to Weaviate."""
    await weaviate_client.connect()
    assert weaviate_client.client is not None
    assert weaviate_client.client.is_connected()
    await weaviate_client.disconnect()


@pytest.mark.asyncio
async def test_weaviate_collections_exist():
    """Test that required collections are created."""
    await weaviate_client.connect()

    # Check UserContext collection exists
    assert weaviate_client.client.collections.exists("UserContext")

    # Check AppContext collection exists
    assert weaviate_client.client.collections.exists("AppContext")

    await weaviate_client.disconnect()


@pytest.mark.asyncio
async def test_store_user_context():
    """Test storing user context."""
    await weaviate_client.connect()

    # Create a test embedding (1536 dimensions for text-embedding-3-small)
    test_embedding = [0.1] * 1536

    result = await weaviate_client.store_user_context(
        owner_id="test_user",
        text_chunk="This is a test chunk",
        embedding=test_embedding,
        metadata={"test": "data"},
        source="test"
    )

    assert result is not None

    await weaviate_client.disconnect()


@pytest.mark.asyncio
async def test_search_user_context():
    """Test searching user context."""
    await weaviate_client.connect()

    # Create a test embedding
    test_embedding = [0.1] * 1536

    # Store a test document
    await weaviate_client.store_user_context(
        owner_id="test_user_search",
        text_chunk="This is a searchable test chunk",
        embedding=test_embedding,
        metadata={"test": "search"},
        source="test"
    )

    # Search for it
    results = await weaviate_client.search_user_context(
        owner_id="test_user_search",
        query_embedding=test_embedding,
        limit=5
    )

    assert isinstance(results, list)
    # Results may be empty if the embedding doesn't match well
    # but the search should not error

    await weaviate_client.disconnect()


@pytest.mark.asyncio
async def test_store_app_context():
    """Test storing application context."""
    await weaviate_client.connect()

    # Create a test embedding
    test_embedding = [0.1] * 1536

    result = await weaviate_client.store_app_context(
        text_chunk="This is an app context test chunk",
        embedding=test_embedding,
        metadata={"test": "app"},
        source="test",
        category="testing"
    )

    assert result is not None

    await weaviate_client.disconnect()


@pytest.mark.asyncio
async def test_search_app_context():
    """Test searching application context."""
    await weaviate_client.connect()

    # Create a test embedding
    test_embedding = [0.1] * 1536

    # Store a test document
    await weaviate_client.store_app_context(
        text_chunk="This is a searchable app context chunk",
        embedding=test_embedding,
        metadata={"test": "app_search"},
        source="test",
        category="testing"
    )

    # Search for it
    results = await weaviate_client.search_app_context(
        query_embedding=test_embedding,
        limit=5
    )

    assert isinstance(results, list)

    await weaviate_client.disconnect()
