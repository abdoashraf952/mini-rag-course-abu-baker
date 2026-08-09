import collections
from models import ChunkModel
from fastapi import APIRouter , status , Request , FastAPI
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest , SearchRequest
from models.ProjectModel import ProjectModel 
from models.ChunkModel import ChunkModel
from controllers.NLPController import NLPController
from models.enums.ResponseEnums import ResponseSignal
from tqdm.auto import tqdm
from tasks.data_indexing import index_data_content
import logging
logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/push/{project_id}")
async def index_project(request:Request , project_id:int,push_request:PushRequest):
    task = index_data_content.delay(project_id,push_request.do_reset)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.DATA_PUSH_TASK_READY.value
        ,"task_id":task.id},
    )


@nlp_router.get("/index/info/{project_id}")  
async def get_index_info(request:Request , project_id:int):

    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.PROJECT_ID_ERROR.value},
        )
    nlp_controller = NLPController(request.app.vector_db_client, request.app.generation_client, request.app.embedding_client, request.app.template_parser)
    
    collection_info = await nlp_controller.get_vector_db_collection_info(project)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.VECTOR_DB_COLLECTION_RETRIEVED.value
        ,"collection_info":collection_info},
    )
    

@nlp_router.get("/index/search/{project_id}")
async def search_in_vector_db(request:Request , project_id:int , search_request:SearchRequest=None, text:str=None , limit:int = 10):

    # Support both GET (query params) and POST (JSON body)
    search_text = search_request.text if search_request else text
    search_limit = search_request.limit if search_request else limit

    if not search_text:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Field 'text' is required"},
        )

    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.PROJECT_ID_ERROR.value},
        )
    nlp_controller = NLPController(request.app.vector_db_client,request.app.generation_client,request.app.embedding_client,request.app.template_parser)
    
    results= await nlp_controller.search_vector_db_collection(project,search_text,search_limit)
    
    if not results:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.SEARCH_IN_VECTOR_DB_ERROR.value},
        )
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.SEARCH_IN_VECTOR_DB_SUCCESS.value
        ,"results":[result.dict() if hasattr(result, "dict") else result for result in results]},
    )

@nlp_router.get("/index/answer/{project_id}")
async def answer_rag_question(request: Request, project_id: int, search_request: SearchRequest = None, text: str = None, limit: int = 10):

    search_text = search_request.text if search_request else text
    search_limit = search_request.limit if search_request else limit

    if not search_text:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Field 'text' is required"},
        )

    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id)

    nlp_controller = NLPController(request.app.vector_db_client, request.app.generation_client, request.app.embedding_client, request.app.template_parser)

    answer, full_prompt, chat_history = await nlp_controller.answer_rag_qustion(project, search_text, search_limit)

    if not answer:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.ANSWER_RAG_QUESTION_ERROR.value},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.ANSWER_RAG_QUESTION_SUCCESS.value,
                  "answer": answer, "full_prompt": full_prompt, "chat_history": chat_history},
    )