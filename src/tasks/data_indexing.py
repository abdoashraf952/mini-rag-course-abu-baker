from celery_app import celery_app , get_setup_utils
from helpers.config import get_settings 
import asyncio
import logging
from controllers.NLPController import NLPController
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.enums.ResponseEnums import ResponseSignal
from tqdm.auto import tqdm
logger = logging.getLogger("celery.task")

@celery_app.task(bind=True,name="tasks.data_indexing.index_data_content",
                    autoretry_for=(Exception,), # Retry on any exception
                    retry_kwargs={"max_retries":3, "countdown":60},)

def index_data_content(self,project_id,do_reset):

    return asyncio.run(
        _index_data_content(self,project_id,do_reset)
    )
async def _index_data_content(task_instance,project_id,do_reset):
    db_engine = None
    vector_db_client = None

    try:
        (db_engine, db_client,generation_client, embedding_client,
        vector_db_client, template_parser,llm_provider_factory
        ,vectordb_provider_factory) = await get_setup_utils()

        logger.warning("Starting indexing for project")

        project_model = await ProjectModel.create_instance(db_client)
        project = await project_model.get_project_or_create_one(project_id)

        if not project:
            task_instance.update_state(
                state='FAILURE',
                meta={'error': ResponseSignal.PROJECT_ID_ERROR.value},
            )

            raise Exception(ResponseSignal.PROJECT_ID_ERROR.value)

        nlp_controller = NLPController(vector_db_client, generation_client, embedding_client, template_parser)

        chunk_model = await ChunkModel.create_instance(db_client)
        has_records=True
        page_no=1
        isersted_item_count=0

        collection_name= nlp_controller.create_collection_name(project_id=project_id)

        _ = await nlp_controller.vector_client.create_collection(
            collection_name=collection_name,
            embedding_size=embedding_client.embedding_size,
            do_reset=do_reset
            )

        total_chunk_count = await chunk_model.get_total_chunks_count(project_id=project.project_id)
        pbar = tqdm(total=total_chunk_count, desc=f"Indexing Project {project_id}",position=0)

        while has_records:
            chunks = await chunk_model.get_DataChunks(project_id=project.project_id, page_no=page_no)
            if len(chunks):
                page_no+=1

            if not chunks or len(chunks)==0:
                has_records=False
                break
                
            chunks_ids = [chunk.chunk_id for chunk in chunks]

            is_inserted = await nlp_controller.index_into_vector_db(
                project=project,
                chunks=chunks,
                chunks_ids=chunks_ids,
            )

            if not is_inserted:
                task_instance.update_state(
                    state='FAILURE',
                    meta={'error': ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value},
                )

                raise Exception(ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value)
                
            pbar.update(len(chunks))
            
            isersted_item_count+=len(chunks)
        task_instance.update_state(
            state='SUCCESS',
            meta={'signal': ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value
            }
        )

        return {
            "signal": ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value
            ,"isersted_item_count":isersted_item_count
        }

        
    except Exception as e:
        logger.error(f"Error while processing file: {e}")
        
        raise 
    finally:
        try:
            if db_engine:
                await db_engine.dispose()
            if vector_db_client:
                await vector_db_client.disconnect()
        except Exception as e:
            logger.error(f"Error while disposing db client: {e}")