import asyncio

import httpx
from app.worker import celery
import asyncpg
from PIL import Image
from io import BytesIO
import os

from app.core.config import settings

DATABASE_URL = settings.DBURL


async def fetch_image_record(conn, image_id):
    query = "SELECT image FROM parser_api_games WHERE game_id = $1"
    return await conn.fetchrow(query, image_id)


async def update_processed_image_url(conn, image_id, link):
    query = "UPDATE parser_api_games SET image = $1 WHERE id = $2"
    await conn.execute(query, link, image_id)


async def download_image(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))


async def process(image_id):
    conn = await asyncpg.connect(DATABASE_URL)
    static_path = os.path.join(os.path.dirname(__file__), '../static')
    try:
        record = await fetch_image_record(conn, image_id)
        if record:
            image_url = record['image']
            original = await download_image(image_url)
            watermark = Image.open(f'{static_path}/watermark.png').convert("RGBA")
            original_width, original_height = original.size
            watermark_width = int(original_width * 0.17)  # Например, 30% от ширины оригинала
            watermark = watermark.resize((watermark_width, int(watermark.height * (watermark_width / watermark.width))),
                                         Image.LANCZOS)
            top_padding = int(original_height * 0.06)
            left_padding = top_padding
            position = (left_padding, top_padding)
            original.paste(watermark, position, watermark)

            output_filename = f"{static_path}/images/{image_id}.jpg"
            original.save(output_filename)
            link = f"{settings.SERVER_HOST}/images/{image_id}.jpg"
            # await update_processed_image_url(conn, image_id, link)
    finally:
        await conn.close()


@celery.task(name='process_image')
def process_image(image_id):
    asyncio.run(process(image_id))
