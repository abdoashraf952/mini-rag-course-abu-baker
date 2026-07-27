from fastapi import APIRouter, Depends
from helpers.config import get_settings , Settings


router = APIRouter(
    prefix="/api/v1",
    tags=["Base"]
)

@router.get("/")
async def wellcome(settings : Settings = Depends(get_settings)):
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}
