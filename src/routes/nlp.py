from models import ChunkModel
from fastapi import APIRouter , status , Request , FastAPI
from fastapi.responses import JSONResponse
from routes.schemes.nlp import PushRequest , SearchRequest
from models.ProjectModel import ProjectModel 
from models.ChunkModel import ChunkModel
from controllers.NLPController import NLPController
from models.enums.ResponseEnums import ResponseSignal

import logging
logger = logging.getLogger('uvicorn.error')

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/push/{project_id}")
async def index_project(request:Request , project_id:str,push_request:PushRequest):

    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.PROJECT_ID_ERROR.value},
        )
    nlp_controller = NLPController(request.app.vector_db_client,request.app.generation_client,request.app.embedding_client)

    chunk_model = await ChunkModel.create_instance(request.app.db_client)
    has_records=True
    page_no=1
    isersted_item_count=0
    idx=0

    while has_records:
        chunks = await chunk_model.get_data_chunks(project_id=project.id,page_no=page_no)
        if len(chunks):
            page_no+=1

        if not chunks or len(chunks)==0:
            has_records=False
            break
            
        chunks_ids = list(range(idx, idx + len(chunks)))
        idx += len(chunks)

        is_inserted = nlp_controller.index_into_vector_db(
            project=project,
            chunks=chunks,
            chunks_ids=chunks_ids,
            do_reset=(push_request.do_reset if page_no == 2 else False)
        )

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": ResponseSignal.INSERT_INTO_VECTOR_DB_ERROR.value},
            )
        
        isersted_item_count+=len(chunks)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.INSERT_INTO_VECTOR_DB_SUCCESS.value
        ,"isersted_item_count":isersted_item_count},
    )

    

@nlp_router.get("/index/info/{project_id}")  
async def get_index_info(request:Request , project_id:str):

    project_model = await ProjectModel.create_instance(request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.PROJECT_ID_ERROR.value},
        )
    nlp_controller = NLPController(request.app.vector_db_client,request.app.generation_client,request.app.embedding_client)
    
    collection_info = nlp_controller.get_vector_db_collection_info(project)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.VECTOR_DB_COLLECTION_RETRIEVED.value
        ,"collection_info":collection_info},
    )
    

@nlp_router.get("/index/search/{project_id}")
async def search_in_vector_db(request:Request , project_id:str , search_request:SearchRequest=None, text:str=None , limit:int = 10):

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
    nlp_controller = NLPController(request.app.vector_db_client,request.app.generation_client,request.app.embedding_client)
    
    results=nlp_controller.search_vector_db_collection(project,search_text,search_limit)
    
    if not results:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": ResponseSignal.SEARCH_IN_VECTOR_DB_ERROR.value},
        )
        
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseSignal.SEARCH_IN_VECTOR_DB_SUCCESS.value
        ,"results":results},
    )