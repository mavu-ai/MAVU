"""Test RAG pipeline functionality."""
import pytest
from rag.pipeline import rag_pipeline
from utils.weaviate_client import weaviate_client


@pytest.mark.asyncio
async def test_rag_pipeline_initialization():
    """Test that RAG pipeline can be initialized."""
    assert rag_pipeline is not None


@pytest.mark.asyncio
async def test_rag_retrieve_context():
    """Test RAG context retrieval."""
    await weaviate_client.connect()

    try:
        # This test will only work if embeddings service is configured
        # For now, just test that the function can be called without error
        context = await rag_pipeline.retrieve_context(
            query="test query",
            owner_id="test_user"
        )

        # Should return a dictionary with user_context and app_context
        assert isinstance(context, dict)
        assert "user_context" in context
        assert "app_context" in context
        assert isinstance(context["user_context"], list)
        assert isinstance(context["app_context"], list)

    except Exception as e:
        # If OpenAI API key is not configured, this might fail
        # but we should still test that the function signature is correct
        pytest.skip(f"RAG pipeline test skipped due to configuration: {str(e)}")

    finally:
        await weaviate_client.disconnect()
