from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Depends
from starlette.middleware.cors import CORSMiddleware

from common import get_logger
from convert.models import ConvertVideoDto
from convert.video_convert import convert_video
from download.models import DownloadVideoDto
from download.video_download import download_video
from resources import secret
from search.video_search import search_videos
from stream.video_stream import StreamVideo

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = get_logger()


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


@app.get("/video/search", dependencies=[Depends(check_apikey)])
async def search(query: str, rows: int = 10):
    try:
        return {"message": "success", "data": search_videos(query, rows)}
    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}


@app.post("/video/download", dependencies=[Depends(check_apikey)])
async def download(download_video_dto: DownloadVideoDto):
    try:
        return {"message": "success", "data": download_video(video_id=download_video_dto.video_id)}
    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}


@app.post("/video/convert", dependencies=[Depends(check_apikey)])
async def convert(convert_video_dto: ConvertVideoDto):
    try:
        return {"message": "success", "data": convert_video(video_id=convert_video_dto.video_id)}
    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}


@app.get("/streaming/{video_id}/", dependencies=[Depends(check_apikey)])
async def stream(video_id: str):
    try:
        hls_file_path = StreamVideo.download_and_convert(video_id)
        return {"message": "success", "data": hls_file_path}

    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}
