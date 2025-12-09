from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Chat(Base, TimestampMixin):
    """
    Model for storing chat conversation history between users and MAVU.

    Attributes:
        id: Unique identifier for the chat message
        user_id: ID of the user who sent/received the message
        message: The user's message text
        response: MAVU's response text
        processed: Whether this chat has been processed by background workers
        context: JSON object storing multi-layer context used for the response
        created_at: Timestamp when message was created (from TimestampMixin)
        updated_at: Timestamp when message was last updated (from TimestampMixin)

    Relationships:
        user: The user who owns this chat message
    """
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    processed = Column(Boolean, default=False, index=True)
    context = Column(JSON, default=None, nullable=True)  # Stores 3-layer context: level1, level2, level3

    user = relationship("User", back_populates="chats")
