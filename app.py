import os

import uvicorn
from typing import Annotated

import dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from starlette.middleware.cors import CORSMiddleware

from common import get_logger
from search.video_search import search_videos

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
        X_API_KEY: Annotated[str | None, Header(convert_underscores=False)] = None,
        X_API_SECRET: Annotated[str | None, Header(convert_underscores=False)] = None,
):

    if X_API_KEY != os.environ.get('API_KEY'):
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")
    if X_API_SECRET != os.environ.get('API_SECRET'):
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


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, workers=1)
