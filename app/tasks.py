import asyncio
import httpx
import asyncpg
from PIL import Image
from io import BytesIO
import os
from tenacity import retry

from app.worker import celery
from app.core.config import settings

DATABASE_URL = settings.DBURL


async def fetch_image_records(pool, image_ids: list):
    placeholders = ', '.join(f'${i + 1}' for i in range(len(image_ids)))

    query = f"SELECT game_id, image FROM parser_api_turkeygames WHERE game_id IN ({placeholders})"
    async with pool.acquire() as conn:
        return await conn.fetch(query, *image_ids)


async def update_processed_image_url(pool, to_save):
    query = "UPDATE parser_api_turkeygames SET watermark_image = $2, watermark_background= $2 WHERE game_id = $1"
    async with pool.acquire() as conn:
        await conn.executemany(query, to_save)


@retry
async def download_image(image_data):
    async with httpx.AsyncClient() as client:
        response = await client.get(image_data['image'])
        response.raise_for_status()
        return {image_data['game_id']: Image.open(BytesIO(response.content))}


async def process(ids: list[str]):
    to_save = []
    static_path = os.path.join(os.path.dirname(__file__), '../static')
    async with asyncpg.create_pool(DATABASE_URL) as pool:

        image_urls = await fetch_image_records(pool, ids)
        image_urls = [dict(i) for i in image_urls]
        tasks = []
        for image in image_urls:
            tasks.append(asyncio.create_task(download_image(image)))
        result = await asyncio.gather(*tasks)
        watermark = Image.open(f'{static_path}/watermark.png').convert("RGBA")
        for image in result:
            game_id, original = image.popitem()
            original_width, original_height = original.size
            watermark_width = int(original_width * 0.17)  # Например, 30% от ширины оригинала
            watermark = watermark.resize((watermark_width, int(watermark.height * (watermark_width / watermark.width))),
                                         Image.LANCZOS)
            top_padding = int(original_height * 0.06)
            left_padding = top_padding
            position = (left_padding, top_padding)
            original.paste(watermark, position, watermark)

            output_filename = f"{static_path}/images/{game_id}.jpg"
            try:
                original.save(output_filename)
            except Exception as e:
                original = original.convert("RGB")
                original.save(output_filename)
            link = f"{settings.SERVER_HOST}/images/{game_id}.jpg"
            to_save.append((game_id, link))
        await update_processed_image_url(pool, to_save)


@celery.task(name='process_image')
def process_image(image_ids):
    asyncio.run(process(image_ids))
