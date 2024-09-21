from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

from app.tasks import process_image
from app.schemas import ImageId

app = FastAPI()


@app.post("/images/")
async def process_images(image_ids: ImageId):
    for image_id in image_ids.ids:
        process_image.delay(image_id)
    return {"message": "Images are being processed"}


@app.get("/image/{id}")
async def process_images(id: str):
    process_image.delay(id)
    return {"message": "Images are being processed"}


@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join('static/images', filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Image not found"}
