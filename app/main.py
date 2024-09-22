import redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
import os

from app.core.config import settings
from app.tasks import process_image
from app.schemas import ImageId

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key")
redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Access denied")


@app.post("/images/", dependencies=[Depends(verify_api_key)])
async def process_images(image_ids: ImageId):
    process_image.delay(image_ids.ids)
    return {"message": "Images are being processed"}


@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join('static/images', filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/tasks/")
async def get_pending_tasks():
    pending_tasks = redis_client.llen('celery')

    return {"pending_tasks": pending_tasks}
