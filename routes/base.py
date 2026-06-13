from fastapi import APIRouter, Depends
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/v1",
    tags=["Base"]
)

@router.get("/health")
def health_check():
    app_name = os.getenv("APP_NAME")
    app_version = os.getenv("APP_VERSION")
    return {"name": app_name, "version": app_version}
