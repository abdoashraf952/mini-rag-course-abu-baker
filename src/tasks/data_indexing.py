from celery_app import celery_app , get_setup_utils
from helpers.config import get_settings 
import asyncio

@celery_app.task(bind=True,name="tasks.data_indexing.index_data_content",
                    autoretry_for=(Exception,), # Retry on any exception
                    retry_kwargs={"max_retries":3, "countdown":60},)

def index_data_content(self,project_id,do_reset):

    return asyncio.run(
        _index_data_content(self,project_id,do_reset)
    )
async def _index_data_content(self,project_id,do_reset):

    pass