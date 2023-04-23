from pydantic import BaseModel


class DownloadVideoDto(BaseModel):
    youtube_url: str
