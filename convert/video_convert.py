import os

import ffmpeg

from convert.config import VideoConvertConfig

INPUT_VIDEO_DIRECTORY = VideoConvertConfig.TARGET_VIDEO_TO_CONVERT_DIRECTORY_LOCAL
OUTPUT_VIDEO_DIRECTORY = VideoConvertConfig.CONVERTED_VIDEO_OUTPUT_DIRECTORY_LOCAL
INPUT_VIDEO_FORMAT = VideoConvertConfig.CONVERT_VIDEO_IN_FORMAT
OUTPUT_VIDEO_FORMAT = VideoConvertConfig.CONVERT_VIDEO_OUT_FORMAT


def convert_video(video_id):
    input_file = f'{INPUT_VIDEO_DIRECTORY}/{video_id}.{INPUT_VIDEO_FORMAT}'
    output_file = f'{OUTPUT_VIDEO_DIRECTORY}/{video_id}/{video_id}.{OUTPUT_VIDEO_FORMAT}'
    output_dir = f'{OUTPUT_VIDEO_DIRECTORY}/{video_id}'
    if os.path.exists(output_dir):
        pass # skip
    else:
        input_stream = ffmpeg.input(input_file, f=INPUT_VIDEO_FORMAT)
        output_stream = ffmpeg.output(input_stream, output_file, format='hls',
                                      start_number=0, hls_time=5, hls_list_size=0)
        ffmpeg.run(output_stream)
