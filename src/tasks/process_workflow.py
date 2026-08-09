from celery import chain
from celery_app import celery_app 
import asyncio
import logging
from tasks.file_processing import process_project_files
from tasks.data_indexing import _index_data_content

logger = logging.getLogger("celery.task")

@celery_app.task(bind=True,name="tasks.process_workflow.push_after_process_task",
                    autoretry_for=(Exception,),
                    retry_kwargs={"max_retries":3, "countdown":60},)
def push_after_process_task(self,prev_task_result,project_id:int,do_reset:int):

    task_result = asyncio.run(
        _index_data_content(self,project_id,do_reset)
    )

    return {
        "project_id":project_id,
        "do_reset":do_reset,
        "task_result":task_result
    }
    

@celery_app.task(bind=True,name="tasks.process_workflow.process_and_push_data",
                    autoretry_for=(Exception,), # Retry on any exception
                    retry_kwargs={"max_retries":3, "countdown":60},)
def process_and_push_data(self,project_id:int,file_id:int,chunk_size:int,overlap_size:int,do_reset:int):
    
    workflow = chain(
        process_project_files.s(project_id=project_id,file_id=file_id,chunk_size=chunk_size,overlap_size=overlap_size,do_reset=do_reset),
        push_after_process_task.s(project_id=project_id,do_reset=do_reset)
    )
    result=workflow.apply_async()

    return {
        "workflow_id":result.id,
        "process_project_files_task_id":result.parent.id,
        "push_after_process_task_id":result.id
    }

