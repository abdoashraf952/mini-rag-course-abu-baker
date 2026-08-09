import hashlib
import json
from datetime import datetime, timezone,timedelta
from sqlalchemy import select,delete
from models.db_schemes.minirag.schemes.celery_task_execution import CeleryTaskExecution


class IdempotencyManager:
    def __init__(self,db_client,db_engine):
        self.db_client = db_client
        self.db_engine = db_engine
        
    def create_args_hash(self,task_name:str,task_args:dict):
        
        combined_args = {
            **task_args,
            "task_name":task_name,
        }
        args_json_string = json.dumps(combined_args,sort_keys=True,default=str)
        return hashlib.sha256(args_json_string.encode()).hexdigest()
        
    async def create_task_record(self,task_name:str,task_args:dict,celery_task_id:str=None)->CeleryTaskExecution:
        args_hash=self.create_args_hash(task_name,task_args)

        task_recerd =CeleryTaskExecution(
            task_name=task_name,
            task_args_hash=args_hash,
            task_args=task_args,
            celery_task_id=celery_task_id,
            status="PENDING",
            started_at=datetime.now(timezone.utc),
        )

        async with self.db_client() as session:
            session.add(task_recerd)
            await session.commit()
            await session.refresh(task_recerd)
        return task_recerd

    async def update_task_status(self,execution_id:int,status:str,result:dict=None):

        async with self.db_client() as session:
            task_record= await session.get(CeleryTaskExecution,execution_id)
            if task_record:
                task_record.status = status

                if result:
                    task_record.result = result
                if status == "SUCCESS" or status == "FAILURE":
                    task_record.completed_at = datetime.now(timezone.utc)
                await session.commit()

    async def get_existing_task(self,task_name:str,task_args:dict,celery_task_id:str=None):
        args_hash = self.create_args_hash(task_name,task_args)
        async with self.db_client() as session:
            result = await session.execute(
                select(CeleryTaskExecution).where(
                    CeleryTaskExecution.task_name == task_name,
                    CeleryTaskExecution.task_args_hash == args_hash,
                    CeleryTaskExecution.celery_task_id == celery_task_id,
                )
            )
            return result.scalar_one_or_none()

    async def should_execute_task(self,task_name:str,task_args:dict ,task_time_limit:int=600,celery_task_id:str=None)->tuple[bool,CeleryTaskExecution]:
        existing_task = await self.get_existing_task(task_name,task_args,celery_task_id)
        if not existing_task:
            return True,None

        if existing_task.status == "SUCCESS":
            return False,existing_task

        if existing_task.status in ["PENDING","RETRY","STARTED"]:
            if existing_task.started_at :
                time_elapsed= (datetime.now(timezone.utc) - existing_task.started_at).total_seconds()
                if time_elapsed>task_time_limit+60:
                    return True,existing_task
            return False,existing_task

        return True,existing_task

    
    async def cleanup_old_tasks(self,timme_retention:int = 86400):

        cutoff_datetime = datetime.now(timezone.utc) - timedelta(seconds=timme_retention)

        session =self.db_client()
        try:
            stmt=delete(CeleryTaskExecution).where(
                CeleryTaskExecution.completed_at< cutoff_datetime,
                
            )
            result=await session.execute(stmt)
            await session.commit()
            return result.rowcount
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
    
        
        
        
        
        
