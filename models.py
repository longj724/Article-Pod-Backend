from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .db import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    feed_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=func.now())
    
    articles = relationship(
        "Article",
        back_populates="user"
    )

class Article(Base):
    __tablename__ = "articles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String)
    content = Column(String, nullable=True)
    content_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now()) 
    speech_model = Column(String, nullable=False)
    audio_url = Column(String, nullable=True)

    user = relationship("User", back_populates="articles")
