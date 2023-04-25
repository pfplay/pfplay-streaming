from pydantic import BaseModel


class DownloadVideoDto(BaseModel):
    video_id: str
