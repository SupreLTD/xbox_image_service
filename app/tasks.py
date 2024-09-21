import asyncio

import httpx
from celery import shared_task
import asyncpg
from PIL import Image
from io import BytesIO
import os

from app.core.config import settings

DATABASE_URL = settings.DBURL

async def fetch_image_record(conn, image_id):
    query = "SELECT image FROM parser_api_games WHERE game_id = $1"
    return await conn.fetchrow(query, image_id)

async def update_processed_image_url(conn, image_id, filename):
    query = "UPDATE parser_api_games SET image = $1 WHERE id = $2"
    await conn.execute(query, f"/images/{filename}", image_id)


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
            watermark_width = int(original_width * 0.6)
            watermark = watermark.resize((watermark_width, int(watermark.height * (watermark_width / watermark.width))),
                                         Image.LANCZOS)

            watermark_width, watermark_height = watermark.size
            top_padding = int(original_height * 0.02)  # Рассчитываем отступ от верха как процент от высоты оригинала
            position = ((original_width - watermark_width) // 2, top_padding)
            original.paste(watermark, position, watermark)

            output_filename = f"{static_path}/images/{image_id}.png"
            original.save(output_filename)
            # await update_processed_image_url(conn, image_id, output_filename)
    finally:
        await conn.close()


@shared_task(name='process_image')
def process_image(image_id):
    asyncio.run(process(image_id))






