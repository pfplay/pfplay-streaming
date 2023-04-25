from pydantic import BaseModel


class ConvertVideoDto(BaseModel):
    video_id: str
