"""SQLAlchemy models for Memory service."""
from __future__ import annotations

import json
from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserMemoryModel(Base):
    __tablename__ = "user_memory"
    user_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), primary_key=True)
    facts = Column(Text, default="{}")
    preferences = Column(Text, default="{}")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SessionTurnModel(Base):
    __tablename__ = "session_turns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
