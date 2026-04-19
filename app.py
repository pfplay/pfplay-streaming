import os

import uvicorn
from typing import Annotated

import dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from pytube import YouTube
from starlette.middleware.cors import CORSMiddleware

from common import get_logger
from search.video_search import search_videos, fetch_videos

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = get_logger()
ENV_PATH = os.environ.get('env_path')
dotenv.load_dotenv(ENV_PATH)


def check_apikey(
        api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
        api_secret: Annotated[str | None, Header(alias="X-Api-Secret")] = None,
):
    if api_key != os.environ.get('API_KEY'):
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")
    if api_secret != os.environ.get('API_SECRET'):
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")


@app.get("/hello")
def health_check():
    return {"message": "OK"}


@app.get("/api/v1/video/search", dependencies=[Depends(check_apikey)])
async def search(query: str, rows: int = 50):
    try:
        data = await search_videos(query, rows)
        return {"message": "success", "data": data}
    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}


@app.get("/api/v1/video/fetch", dependencies=[Depends(check_apikey)])
async def fetch(url: str):
    try:
        data = await fetch_videos(url)
        return {"message": "success", "data": [data]}
    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, workers=1)
