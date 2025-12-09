from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Threat(Base, TimestampMixin):
    """
    Model for storing detected threats in user conversations.

    Attributes:
        id: Unique identifier
        user_id: ID of the user associated with the threat
        threat_type: Category of threat detected
        severity: Severity level of the threat
        description: Detailed description of the threat
        evidence: Specific quotes or evidence from conversation
        detected_at: When the threat was detected
        resolved: Whether the threat has been addressed
        resolved_at: When the threat was resolved
        resolved_by: Who resolved the threat
        notes: Additional notes about the threat or resolution
    """
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    threat_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)

    description = Column(Text, nullable=False)
    evidence = Column(Text)

    detected_at = Column(DateTime, default=datetime.now, nullable=False)
    resolved = Column(Integer, default=0)  # Boolean: 0 = unresolved, 1 = resolved
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="threats")
