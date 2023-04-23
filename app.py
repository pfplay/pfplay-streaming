from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Depends
from download.model import DownloadVideoDto
from download.video_download import download_video
from resources import secret
from search.video_search import search_videos

app = FastAPI()


async def check_apikey(
        api_key: Annotated[str | None, Header(convert_underscores=False)] = None,
        api_secret: Annotated[str | None, Header(convert_underscores=False)] = None,
):
    if api_key != secret.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")
    if api_secret != secret.API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")


@app.get("/hello")
async def health_check():
    return {"message": "OK"}


@app.post("/video/download", dependencies=[Depends(check_apikey)])
async def play_streaming_video(download_video_dto: DownloadVideoDto):
    download_video(youtube_url=download_video_dto.youtube_url)
    return {"message": "success"}


@app.get("/video/search", dependencies=[Depends(check_apikey)])
async def search_video(query: str, rows: int = 10):
    return {"message": "success", "data": search_videos(query, rows)}
