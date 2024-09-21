import base64
import secrets
from typing import Any, Dict, List, Optional, Union
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    DBURL: str

    class Config:
        env_file = data_path = os.path.join(os.path.dirname(__file__), '../.env')
        env_file_encoding = 'utf-8'


settings = Settings()
