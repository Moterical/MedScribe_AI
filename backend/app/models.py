from sqlalchemy import Column, Integer, String, Date, Time, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=False)
    interaction_type = Column(String(50), default="Meeting")
    interaction_date = Column(Date, nullable=False)
    interaction_time = Column(Time, nullable=False)
    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    sentiment = Column(String(20), default="Neutral")
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    email_draft = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    samples = relationship("Sample", back_populates="interaction", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="interaction", cascade="all, delete-orphan")


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    sample_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)

    interaction = relationship("Interaction", back_populates="samples")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="CASCADE"), nullable=False)
    material_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)

    interaction = relationship("Interaction", back_populates="materials")
