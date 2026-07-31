# PFPlay-streaming

PFPlay 의 **YouTube 메타데이터 사이드카**. `pfplay-platform` 백엔드가 음악 검색과 URL 해소를
이 서비스에 위임한다.

> 실사 기준: 2026-07-31 (`master`).
> 이 서비스가 죽으면 **음악 검색만** 실패한다(파티룸·재생·채팅은 정상).

## 역할

| 하는 일 | 하지 않는 일 |
|---|---|
| 검색어 → YouTube 영상 메타데이터 목록 | 오디오/비디오 다운로드·변환 |
| YouTube URL → 단일 영상 메타데이터 | 스트리밍 서빙(과거 nginx-rtmp 실험은 폐기) |

플랫폼 쪽 소비 지점: `playlist` 모듈의 `YoutubeSearchService` 인터페이스 →
유일 구현 `PytubeSearchService`. 즉 **플랫폼은 YouTube Data API 키를 갖고 있지 않다.**

## 런타임

| 항목 | 값 |
|---|---|
| Python | 3.11 |
| 프레임워크 | FastAPI + uvicorn |
| 포트 | 9000 |
| 워커 | **1** (Docker `CMD` 기준) |
| 핵심 의존 | `pytube 15.0.0`(고정), `aiohttp`, `python-dotenv`, `ffmpeg-python`(레거시) |
| CORS | 전면 허용(`allow_origins=["*"]`) — 인증은 API 키 헤더가 담당 |

## API

모든 `/api/v1/**` 엔드포인트는 아래 두 헤더를 요구한다. 하나라도 불일치면 **401**.

```
X-Api-Key:    $API_KEY
X-Api-Secret: $API_SECRET
```

### `GET /hello`

헬스체크. 인증 불필요.

```json
{"message": "OK"}
```

### `GET /api/v1/video/search?query={q}&rows={n}`

검색어로 영상 목록을 반환한다. `rows` 기본값 50 (플랫폼은 10으로 호출한다).

```json
{
  "message": "success",
  "data": [
    {
      "video_id": "gL6sQ6za3f8",
      "video_title": "Jon Sable - Shoplifters",
      "watch_url": "https://www.youtube.com/watch?v=gL6sQ6za3f8",
      "embed_url": "https://www.youtube.com/embed/gL6sQ6za3f8",
      "author": "채널명",
      "running_time": "7:46",
      "thumbnail_url": "https://i.ytimg.com/vi/..."
    }
  ]
}
```

### `GET /api/v1/video/fetch?url={youtube_url}`

URL 하나를 해소해 **길이 1의 배열**로 반환한다(형태를 검색과 맞추기 위함).

## ⚠️ 응답 계약의 함정

**예외가 나도 HTTP 200 이다.** 두 엔드포인트 모두 `try/except` 로 예외를 삼키고 다음을 돌려준다.

```json
{"message": "error", "data": ""}
```

즉 **`data` 의 타입이 성공 시 배열, 실패 시 빈 문자열**로 바뀐다. 소비자(플랫폼)가 배열로
역직렬화하다 실패하며, 이때 클라이언트에 보이는 증상은 "검색 모달 에러" 다 — 원인을 이 서비스가
아니라 플랫폼에서 찾게 되기 쉽다.

- 실패 여부는 상태 코드가 아니라 **`message` 필드**로 판단해야 한다.
- 실제 원인은 이 서비스의 **stdout 로그**(`asctime|levelname|file:line|message`)에 남는다.

## ⚠️ pytube 15 의 현재 상태

- 검색 경로는 pytube 의 `Search` 를 상속한 자체 비동기 구현(`search/video_search.py`)이 innertube
  WEB 클라이언트를 직접 호출한다. **YouTube 가 응답 구조를 바꾸면 파싱이 조용히 깨진다.**
- 광고·shelf·radio(mix)·playlist·channel 결과는 걸러내지만, **Shorts 는 일반 `videoRenderer`
  로 오기 때문에 구조적으로 배제할 수 없다.**
- `running_time` 은 `lengthText` 가 없는 항목(라이브 등)에서 `None` 이 된다.
- pytube 15.0.0 은 player 경로가 깨져 있어 재생 가능 여부(embed 허용 등) 판정에 쓸 수 없다.

→ 이 때문에 **yt-dlp 마이그레이션 + `playable_in_embed` 사전 태깅**이 이슈
[#11](https://github.com/pfplay/pfplay-streaming/issues/11) 로 열려 있다.

## 환경변수

`env_path` 가 가리키는 dotenv 파일 또는 프로세스 환경에서 읽는다.

| 변수 | 뜻 |
|---|---|
| `env_path` | dotenv 파일 경로 (선택) |
| `API_KEY` | `X-Api-Key` 검증 값 |
| `API_SECRET` | `X-Api-Secret` 검증 값 |

플랫폼 쪽 대응 설정은 `PYTUBE_URI` / `PYTUBE_API_KEY` / `PYTUBE_API_SECRET` 이다. 양쪽 값이
어긋나면 검색이 전부 401 이 된다.

## 로컬 실행

### Poetry

```bash
poetry install
API_KEY=local API_SECRET=local poetry run uvicorn app:app --host 0.0.0.0 --port 9000
```

### Docker

```bash
docker build -t pfplay-streaming .
docker run -d --name pfplay-streaming -p 9000:9000 \
  -e API_KEY=local -e API_SECRET=local pfplay-streaming

curl http://localhost:9000/hello
# {"message":"OK"}

curl -H 'X-Api-Key: local' -H 'X-Api-Secret: local' \
  'http://localhost:9000/api/v1/video/search?query=jon%20sable&rows=5'
```

정지 / 재시작 / 이미지 재빌드:

```bash
docker stop pfplay-streaming
docker start pfplay-streaming
docker rm -f pfplay-streaming && docker build -t pfplay-streaming .
```

### 플랫폼과 함께 띄우기

플랫폼 레포의 compose 가 이 디렉터리를 `pytube` 서비스로 빌드한다
(`build.context: ../pfplay-streaming`). 즉 **두 레포가 형제 디렉터리로 놓여 있어야 한다.**

```bash
# pfplay-platform 에서
docker compose -f docker-compose.local.yml -p pfplay-local --env-file .env.local up -d --build
```

> `up -d app` 만 실행하면 이 사이드카는 뜨지 않는다 — 앱은 정상인데 검색만 실패한다.

## 파일 구조

```
app.py                  # FastAPI 앱: 인증 의존성 + 3개 엔드포인트
common.py               # stdout 로거
model/models.py         # Video (pydantic dataclass)
search/video_search.py  # pytube Search 비동기 상속 구현 + innertube 호출
Dockerfile              # poetry export → pip install 2-stage 빌드
run.sh                  # 레거시 기동 스크립트 (Dockerfile 에서 미사용, workers=4)
```

## 레거시

초기에는 nginx-rtmp + ffmpeg 로 실제 스트리밍을 서빙하려 했다(`ffmpeg-python` 의존과 `run.sh` 가
그 흔적이다). 현재 코드는 **메타데이터만** 다루며 그 경로는 사용하지 않는다.
