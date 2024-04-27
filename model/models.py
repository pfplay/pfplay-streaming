from pydantic.dataclasses import dataclass


@dataclass
class Video:
    video_id: str
    video_title: str
    watch_url: str
    embed_url: str
    author: str
    running_time: str
    thumbnail_url: str

