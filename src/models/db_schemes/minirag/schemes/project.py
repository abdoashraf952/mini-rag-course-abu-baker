from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, String,DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship


class Project(SQLAlchemyBase):
    __tablename__ = 'project'

    project_id = Column(Integer, primary_key=True ,autoincrement=True)
    project_uuid = Column(UUID(as_uuid=True), unique=True , nullable=False , default=uuid4)

    created_at = Column(DateTime , nullable=False , server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    chunks = relationship("DataChunk", back_populates="project")
    assets = relationship("Asset", back_populates="project")
    

