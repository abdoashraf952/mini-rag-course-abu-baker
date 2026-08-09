from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column,Integer,String,DateTime,JSON,func
from sqlalchemy.dialects.postgresql import UUID,JSONB
from sqlalchemy import Index


class CeleryTaskExecution(SQLAlchemyBase):
    __tablename__ = "celery_task_execution"

    execution_id = Column(Integer, primary_key=True,autoincrement=True)

    task_name = Column(String(255),nullable=False)
    task_args_hash = Column(String(64),nullable=False)
    celery_task_id = Column(UUID(as_uuid=True),nullable=False)
    
    status = Column(String(25),nullable=False,default="PENDING")

    task_args = Column(JSONB,nullable=False)
    result = Column(JSONB,nullable=True)

    started_at = Column(DateTime(timezone=True),nullable=True)
    completed_at = Column(DateTime(timezone=True),nullable=True)
    
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    updated_at = Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())

    __table_args__ = (
        Index("ix_task_execution_status", status),
        Index("ix_task_execution_celery_task_id", celery_task_id),
        Index("ix_task_execution_created_at", created_at),
        Index("ix_task_name_task_args_hash_celery_task_id", task_name, task_args_hash,celery_task_id,unique=True),
    )