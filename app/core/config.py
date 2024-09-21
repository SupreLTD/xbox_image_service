import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    DBURL: str
    API_KEY: str

    class Config:
        env_file = data_path = os.path.join(os.path.dirname(__file__), '../.env')
        env_file_encoding = 'utf-8'


settings = Settings()
