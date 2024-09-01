from fastapi import FastAPI, UploadFile, File, BackgroundTasks
import uuid
import asyncpg
from typing import List
from io import BytesIO
from PIL import Image
import aiofiles
import aiohttp
from fastapi.staticfiles import StaticFiles

import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = "postgresql://postgres:start@localhost:5432/image_processing"

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            input_image_urls TEXT[] NOT NULL,
            output_image_urls TEXT[],
            request_id UUID NOT NULL,
            status VARCHAR(50) DEFAULT 'PENDING'
        );
    ''')
    await conn.close()

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Image Processing API!"}

@app.post("/upload/")
async def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    request_id = uuid.uuid4()  # Generate unique request ID
    content = await file.read()
    decoded = content.decode("utf-8").splitlines()
    rows = [row.split(",") for row in decoded]

    conn = await asyncpg.connect(DATABASE_URL)
    for row in rows[1:]:
        product_name = row[1]
        input_image_urls = row[2].split(',')
        await conn.execute('''
            INSERT INTO products (product_name, input_image_urls, request_id)
            VALUES ($1, $2, $3)
        ''', product_name, input_image_urls, request_id)

    await conn.close()

    background_tasks.add_task(process_images, request_id)
    return {"request_id": str(request_id)}

async def process_images(request_id: uuid.UUID):
    logging.info(f"Started processing for request_id: {request_id}")
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('''
        SELECT id, input_image_urls FROM products WHERE request_id = $1
    ''', request_id)

    for row in rows:
        product_id = row['id']
        input_urls = row['input_image_urls']
        output_urls = []

        for url in input_urls:
            logging.info(f"Fetching image from {url}")
            image = await fetch_image(url)
            if image:
                logging.info(f"Compressing image from {url}")
                compressed_image = compress_image(image)
                output_url = await save_image(compressed_image)
                logging.info(f"Image saved to {output_url}")
                output_urls.append(output_url)

        await conn.execute('''
            UPDATE products SET output_image_urls = $1, status = $2 WHERE id = $3
        ''', output_urls, 'COMPLETED', product_id)
    await conn.close()
    logging.info(f"Completed processing for request_id: {request_id}")

async def fetch_image(url: str) -> Image.Image:
    # Clean up the URL
    url = url.strip().strip('"')

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    return Image.open(BytesIO(content))
                else:
                    print(f"Failed to fetch image: {response.status}")
                    return None
        except aiohttp.client_exceptions.InvalidURL as e:
            print(f"Invalid URL: {url} - {str(e)}")
            return None
        except Exception as e:
            print(f"Error fetching image from {url}: {str(e)}")
            return None


def compress_image(image: Image.Image) -> Image.Image:
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=50)
    buffer.seek(0)
    return Image.open(buffer)

async def save_image(image: Image.Image) -> str:
    output_path = f"static/{uuid.uuid4()}.jpg"
    image.save(output_path)
    output_url = f"http://localhost:8000/static/{uuid.uuid4()}.jpg"
    return output_url

@app.get("/status/{request_id}")
async def check_status(request_id: uuid.UUID):
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('''
        SELECT product_name, status, output_image_urls FROM products WHERE request_id = $1
    ''', request_id)
    await conn.close()

    return {"status": [dict(row) for row in rows]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
