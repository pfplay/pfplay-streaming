import os
from common import get_logger
from download.video_download import download_video
from convert.video_convert import convert_video
from convert.config import VideoConvertConfig

INPUT_VIDEO_FORMAT = VideoConvertConfig.CONVERT_VIDEO_IN_FORMAT
OUTPUT_VIDEO_FORMAT = VideoConvertConfig.CONVERT_VIDEO_OUT_FORMAT
OUTPUT_VIDEO_DIRECTORY = VideoConvertConfig.CONVERTED_VIDEO_OUTPUT_DIRECTORY_LOCAL

logger = get_logger()


class StreamVideo:
    @staticmethod
    def download_and_convert(video_id: str):
        try:
            download_video(video_id)
            convert_video(video_id)

            hls_file_path = f"{OUTPUT_VIDEO_DIRECTORY}/{video_id}/{video_id}.{OUTPUT_VIDEO_FORMAT}"

            if not os.path.isfile(hls_file_path):
                raise Exception(f"HLS File not found: {hls_file_path}")

            return hls_file_path

        except Exception as ex:
            logger.error(ex)
            raise ex
