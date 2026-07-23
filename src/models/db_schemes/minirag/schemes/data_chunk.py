from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey , func
from sqlalchemy.dialects.postgresql import UUID , JSONB
from uuid import uuid4
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from pydantic import BaseModel


class DataChunk(SQLAlchemyBase):
    __tablename__ = 'chunks'

    chunk_id = Column(Integer, primary_key=True ,autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), unique=True , nullable=False , default=uuid4)
    
    chunk_text = Column(String , nullable=False)
    chunk_order = Column(Integer , nullable=False)
    chunk_metadata = Column(JSONB , nullable=False)

    created_at = Column(DateTime , nullable=False , server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    chunk_project_id = Column(Integer,ForeignKey('project.project_id') , nullable=False)
    chunk_asset_id = Column(Integer,ForeignKey('asset.asset_id') , nullable=False)

    # relationship
    project = relationship("Project", back_populates="chunks")
    asset   = relationship("Asset", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_chunk_asset_id', chunk_asset_id),
        Index('idx_chunk_project_id', chunk_project_id),
    )

class RetrivedDocument(BaseModel):
    text : str
    score : float