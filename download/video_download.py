from pytube import YouTube

from download.config import YoutubeVideoDownloadConfig

VIDEO_FILE_FORMAT = YoutubeVideoDownloadConfig.DOWNLOAD_VIDEO_FILE_FORMAT
VIDEO_DOWNLOAD_DIRECTORY = YoutubeVideoDownloadConfig.DOWNLOAD_VIDEO_DIRECTORY_LOCAL


def download_video(youtube_url):
    yt = YouTube(youtube_url)
    yt.streams \
        .filter(
            progressive=True,
            only_audio=True,
            file_extension=VIDEO_FILE_FORMAT) \
        .order_by('resolution') \
        .desc() \
        .first() \
        .get_by_itag(22)\
        .download(output_path=VIDEO_DOWNLOAD_DIRECTORY)
