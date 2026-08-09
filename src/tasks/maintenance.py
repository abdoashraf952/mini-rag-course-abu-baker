from celery_app import celery_app,get_setup_utils
from helpers.config import Settings,get_settings
import asyncio
from utils.idempotency_manager import IdempotencyManager
import logging

logger = logging.getLogger("celery.task")


@celery_app.task(name="tasks.maintenance.cleanup_old_task",bind=True,
autoretry_for=(Exception,),
retry_kwargs={"max_retries":3,"countdown":60})

def cleanup_old_task(self):
    
    return asyncio.run(_cleanup_old_task(self))


async def _cleanup_old_task(task_instance):
    
    db_engine,vector_db_client = None,None
    try:
        (db_engine, db_client,generation_client, embedding_client,
        vector_db_client, template_parser,llm_provider_factory
        ,vectordb_provider_factory) = await get_setup_utils()

        idempotency_manager = IdempotencyManager(db_client=db_client,db_engine=db_engine)

        logger.warning("Executing task: cleanup_old_tasks")
        deleted_count = await idempotency_manager.cleanup_old_tasks()
        logger.warning(f"cleanup_old_tasks deleted {deleted_count} record(s)")

        return {"deleted": deleted_count}

    except Exception as e:
        logger.error(f"Error cleaning up old tasks: {e}")
        raise e
    finally:
        if db_engine:
            await db_engine.dispose()
        if vector_db_client:
            await vector_db_client.disconnect()
    

