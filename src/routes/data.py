from fastapi import FastAPI, APIRouter, Depends, UploadFile, status ,Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from routes.schemes.data import ProcessRequest
from models.ProjectModel import ProjectModel
from models.db_schemes.minirag.schemes.data_chunk import DataChunk
from models.db_schemes.minirag.schemes.asset import Asset
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers.NLPController import NLPController
from tasks.file_processing import process_project_files
from tasks.process_workflow import process_and_push_data as process_and_push_data_task

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request,project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    
    project  = await project_model.get_project_or_create_one(project_id=project_id)
    
    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_upload_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )

    
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    
    asset_resource =Asset(
        asset_name=file_id,
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_size = os.path.getsize(file_path)
    ,
    asset_config={},
    )

    asset_record = await asset_model.create_asset(
        asset=asset_resource
    )

    return JSONResponse(
            content={
                "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                "file_id": asset_record.asset_name
            }
        )


@data_router.post("/process/{project_id}")
async def process_data(request: Request,project_id: int, process_request: ProcessRequest):


    task = process_project_files.delay(
        project_id=project_id,
        file_id=process_request.file_id,
        chunk_size=process_request.chunk_size,
        overlap_size=process_request.overlap_size,
        do_reset=process_request.do_reset
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            "task_id":task.id
        }
    )


@data_router.post("/process-and-push/{project_id}")
async def process_and_push_data(request: Request,project_id: int, process_request: ProcessRequest):


    workflow_task = process_and_push_data_task.delay(
        project_id=project_id,
        file_id=process_request.file_id,
        chunk_size=process_request.chunk_size,
        overlap_size=process_request.overlap_size,
        do_reset=process_request.do_reset
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.PROCESS_WORKFLOW_TASK_READY.value,
            "task_id":workflow_task.id
        }
    )