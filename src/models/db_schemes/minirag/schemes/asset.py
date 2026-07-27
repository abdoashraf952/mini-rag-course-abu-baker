from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey ,func
from sqlalchemy.dialects.postgresql import UUID , JSONB
from uuid import uuid4
from sqlalchemy.orm import relationship
from sqlalchemy import Index


class Asset(SQLAlchemyBase):
    __tablename__ = 'asset'

    asset_id = Column(Integer, primary_key=True ,autoincrement=True)
    asset_uuid = Column(UUID(as_uuid=True), unique=True , nullable=False , default=uuid4)
    
    asset_type = Column(String , nullable=False)
    asset_size = Column(Integer , nullable=False)
    asset_name = Column(String , nullable=False)
    asset_config = Column(JSONB , nullable=False)

    created_at = Column(DateTime , nullable=False , server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    asset_project_id = Column(Integer,ForeignKey('project.project_id') , nullable=False)

    # relationship
    project = relationship("Project", back_populates="assets")

    chunks = relationship("DataChunk", back_populates="asset")


    __table_args__ = (
        Index('idx_asset_project_id', asset_project_id),
        Index('idx_asset_type',asset_type),
    )
