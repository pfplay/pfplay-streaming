import uvicorn
import traceback
from typing import Annotated

import dotenv
from fastapi import FastAPI, Header, HTTPException, APIRouter
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware

from common import get_logger
from search.video_search import async_search_videos, search_videos

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = get_logger()
apikey = APIKeyHeader(name="X-API-KEY")
apisecret = APIKeyHeader(name="X-API-SECRET")
# api = APIRouter(prefix='/api/v1')

secrets = dotenv.load_dotenv('config/.env')


def check_apikey(
        api_key: Annotated[str | None, Header(convert_underscores=False)] = None,
        api_secret: Annotated[str | None, Header(convert_underscores=False)] = None,
):
    
    if api_key != secrets.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")
    if api_secret != secrets.API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized api key, secret")
    pass


@app.get("/hello")
def health_check():
    return {"message": "OK"}


# @app.get("/api/v1/video/search", dependencies=[Depends(check_apikey)])
@app.get("/api/v1/video/search")
async def search(query: str, rows: int = 50, limit_video_length: int = -1):
    try:
        data = await async_search_videos(query, rows, limit_video_length)
        return {"message": "success", "data": data}
    except Exception as ex:
        logger.error(ex)
        traceback.format_exc()
        return {"message": "error", "data": ""}


@app.get("/api/v2/video/search")
def search(query: str, rows: int = 50, limit_video_length: int = -1):
    try:
        return {"message": "success", "data": search_videos(query, rows, limit_video_length)}
    except Exception as ex:
        logger.error(ex)
        return {"message": "error", "data": ""}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9000, workers=1)

