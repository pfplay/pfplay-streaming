from common import get_logger
from pytube.contrib.search import Search
from download.exception import VideoLengthLimitExceededException

logging = get_logger()


def search_videos(query, rows=10):
    results = YoutubeSearch(query).results
    res_data = list()
    for video in results:
        try:
            res_data.append({
                'title': video.title,
                'video_id': video.video_id,
                'embed_url': video.embed_url,
                'watch_url': video.watch_url,
                'thumbnail_url': video.thumbnail_url,
                'author': video.author,
            })

            if len(res_data) >= rows:
                break
        except VideoLengthLimitExceededException:
            continue
        except Exception:
            continue

    return res_data


class YoutubeSearch(Search):
    def __init__(self, query):
        super().__init__(query=query)
