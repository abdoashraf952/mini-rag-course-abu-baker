from fastapi import FastAPI
from routes import base , data ,nlp
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm import LLMProviderFactory
from stores.vectorDB import VectorDBProviderFactory

app = FastAPI()
async def startup_span():
    settings = get_settings()
    app.mongodb_conn = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongodb_conn[settings.MONGODB_DATABASE]
    app.generation_client = LLMProviderFactory(settings).create(settings.GENERATION_BACKEMD)
    app.embedding_client = LLMProviderFactory(settings).create(settings.EMBEDDING_BACKEND)
    app.vector_db_client = VectorDBProviderFactory(settings).create(settings.VECTOR_DB_BACKEND)


    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)
    app.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID,settings.EMBEDDING_MODEL_SIZE)

    app.vector_db_client.connect()
    

async def shutdown_span():
    app.mongodb_conn.close()
    app.vector_db_client.disconnect()


app.on_event("shutdown")(shutdown_span)
app.on_event("startup")(startup_span)


app.include_router(base.router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)