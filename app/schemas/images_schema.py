from pydantic import BaseModel


class ImageId(BaseModel):
    ids: list[str]
