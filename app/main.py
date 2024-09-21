from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from app.core.config import settings
import os

from app.tasks import process_image
from app.schemas import ImageId

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Access denied")


@app.post("/images/", dependencies=[Depends(verify_api_key)])
async def process_images(image_ids: ImageId):
    for image_id in image_ids.ids:
        process_image.delay(image_id)
    return {"message": "Images are being processed"}


@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join('static/images', filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Image not found"}
