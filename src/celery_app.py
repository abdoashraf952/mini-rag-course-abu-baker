from helpers.config import get_settings
from celery import Celery
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectorDB import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

settings = get_settings()


async def get_setup_utils():
    settings = get_settings()

    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSEORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"

    db_engine = create_async_engine(postgres_conn)
    db_client = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(config=settings, db_client=db_client)

    # generation client
    generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEMD)
    generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)

    # embedding client
    embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_MODEL_SIZE)
    
    # vector db client
    vector_db_client = vectordb_provider_factory.create(
        provider=settings.VECTOR_DB_BACKEND
    )
    await vector_db_client.connect()

    template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_lang=settings.DEFAULT_LANG,
    )

    return (db_engine, db_client,generation_client, embedding_client, vector_db_client, template_parser,llm_provider_factory,vectordb_provider_factory)



celery_app = Celery(
    "mini_rag",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_BACKEND,
    include=["tasks.file_processing", "tasks.data_indexing","tasks.process_workflow"
    ,"tasks.maintenance"]
)

celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=[settings.CELERY_TASK_SERIALIZER],
    task_acks_late=True,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_ignore_result=True,
    task_expires=3600,
    worker_concurrency=settings.CELERY_WORKER_CONCURNCY,


    broker_connection_retry_on_startup=True,
    broker_connection_retry = True,
    broker_connection_max_retries=10,
    worker_cancel_long_running_tasks_on_connection_loss = True,

    task_routes={
        "tasks.file_processing.process_project_files" : {"queue":"file_processing_queue"},
        "tasks.process_workflow.push_after_process_task" : {"queue":"push_after_process_task_queue"},
        "tasks.data_indexing.index_data_content" : {"queue":"index_data_queue"},
        "tasks.maintenance.cleanup_old_task" : {"queue":"default"}
    }

)
celery_app.conf.beat_schedule = {
    "cleanup_old_tasks":{
        "task": "tasks.maintenance.cleanup_old_task",
        "schedule": 86400,
        "args":()
    },
}
celery_app.conf.timezone = 'UTC'

celery_app.conf.task_default_queue = "default"



