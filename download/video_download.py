from pytube import YouTube

from common import get_logger
from download.config import YoutubeVideoDownloadConfig

VIDEO_FILE_FORMAT = YoutubeVideoDownloadConfig.DOWNLOAD_VIDEO_FILE_FORMAT
VIDEO_DOWNLOAD_DIRECTORY = YoutubeVideoDownloadConfig.DOWNLOAD_VIDEO_DIRECTORY_LOCAL
VIDEO_WATCH_URL_PREFIX = YoutubeVideoDownloadConfig.YOUTUBE_WATCH_URL_PREFIX

logger = get_logger()


def download_video(video_id):
    youtube_url = f"{VIDEO_WATCH_URL_PREFIX}{video_id}"
    output_video = f"{video_id}.{VIDEO_FILE_FORMAT}"
    try:
        yt = YouTube(youtube_url)
        yt.streams \
            .filter(progressive=True, file_extension=VIDEO_FILE_FORMAT) \
            .order_by('resolution') \
            .desc() \
            .first() \
            .download(output_path=VIDEO_DOWNLOAD_DIRECTORY, filename=output_video)
    except Exception as ex:
        logger.error(f"failed to download video, video id: {video_id}, {ex}")
        raise Exception
    else:
        return video_id
