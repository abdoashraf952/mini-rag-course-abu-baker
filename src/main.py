from fastapi import FastAPI
from routes import base , data ,nlp
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from helpers.config import get_settings
from stores.llm import LLMProviderFactory
from stores.vectorDB import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.orm import sessionmaker

from utils.metrics import setup_metrics

app = FastAPI()

setup_metrics(app)

async def startup_span():
    settings = get_settings()

    app.postgres_conn = create_async_engine(
        f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSEORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}",
        echo=True
    )
    app.db_client = sessionmaker(app.postgres_conn,class_=AsyncSession ,expire_on_commit=False)

    app.generation_client = LLMProviderFactory(settings).create(settings.GENERATION_BACKEMD)
    app.embedding_client = LLMProviderFactory(settings).create(settings.EMBEDDING_BACKEND)
    app.vector_db_client = VectorDBProviderFactory(config=settings,db_client=app.db_client).create(settings.VECTOR_DB_BACKEND)


    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID,settings.EMBEDDING_MODEL_SIZE)

    await app.vector_db_client.connect()

    app.template_parser = TemplateParser(language=settings.PRIMARY_LANG,default_lang=settings.DEFAULT_LANG)
    

async def shutdown_span():
    await app.postgres_conn.dispose()
    await app.vector_db_client.disconnect()


app.on_event("shutdown")(shutdown_span)
app.on_event("startup")(startup_span)


app.include_router(base.router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)