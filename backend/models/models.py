from sqlalchemy import Column, Integer, String, Text, Float, CheckConstraint, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Entry(Base):
    __tablename__ = "entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    raw_transcript = Column(Text)
    symptoms = Column(ARRAY(Text))
    severity = Column(Integer, CheckConstraint('severity >= 1 AND severity <= 10'))
    potential_triggers = Column(ARRAY(Text))
    mood = Column(String(50))
    body_location = Column(ARRAY(Text))
    time_context = Column(String(100))
    notes = Column(Text)
    logged_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Correlation(Base):
    __tablename__ = "correlations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    symptom = Column(String(255))
    trigger = Column(String(255))
    correlation_score = Column(Float)
    sample_size = Column(Integer)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


class InsightsCache(Base):
    __tablename__ = "insights_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    insights_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    entry_count_at_computation = Column(Integer)
