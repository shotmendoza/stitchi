import json
from datetime import datetime
from typing import Optional

import ffmpeg
from dirlin import Path


class ApplicationConfig:
    pass


class Video:
    def __init__(self, file_path: Path):
        """
        An object representing a Video. Holds information regarding the video file.

        Attributes:
            - filepath: the full path, we use this as arguments for ffmpeg functions
            - filename: the name of the video file (i.e. example.mp4)
            - folder_path: the parent folder path (i.e. main_directory/*)
            - meta: holds data regarding the video file

        :param file_path: the pathlib.Path file path to the Video
        """
        self.filename = str(file_path.name)
        self.folder_path = str(file_path.parent)

        # Creation of the Metadata
        _size = f"{round(file_path.stat().st_size * 0.000001, 2)} MB"
        _last_opened = f"{datetime.fromtimestamp(file_path.stat().st_atime)}"
        _last_modified = f"{datetime.fromtimestamp(file_path.stat().st_mtime)}"
        try:
            _created = f"{datetime.fromtimestamp(file_path.stat().st_birthtime)}"
        except AttributeError:
            _created = "Unknown"
        _meta = {
            "size": _size,
            "last_opened": _last_opened,
            "last_modified": _last_modified,
            "created": _created
        }
        self.meta = json.dumps(_meta)
        self._filepath = file_path

    @property
    def filepath(self):
        """
        Full path of the video file. Includes the parent and the filename.
        """
        return str(self._filepath)

    def __repr__(self):
        return f"filename: {self.filename}: {self.meta}"


class VideoEditor:
    @classmethod
    def join_and_save(
            cls,
            base_video: Video,
            new_video: Video,
            output_path: str,
            bv_kw: Optional[dict] = None,
            nv_kw: Optional[dict] = None,
            concat_kw: Optional[dict] = None
    ):
        """
        Appends a new video at the end of the base video. Allows for keywords to be added
        so that you can add transitions to the videos.

        :param base_video: The video the function will append to
        :param new_video: the video that is going to be added at the end of the base video
        :param output_path: where to save the video and the filename
        :param bv_kw: base video keyword arguments for the input function
        :param nv_kw: new video keyword arguments for the input function
        :param concat_kw: keyword arguments for the concat function

        :return:
        """
        kw_args = (bv_kw, nv_kw, concat_kw)
        use_kw_args = [dict() if not kw else kw for kw in kw_args]

        in1 = ffmpeg.input(str(base_video.filepath), **use_kw_args[0])
        in2 = ffmpeg.input(str(new_video.filepath), **use_kw_args[1])

        # base video filtering and updates
        v1 = in1.video
        a1 = in1.audio

        # new video filtering and updates
        v2 = in2.video
        a2 = in2.audio

        joined = ffmpeg.concat(v1, a1, v2, a2, v=1, a=1, **use_kw_args[2]).node
        out = ffmpeg.output(joined[0], joined[1], output_path)
        out.run()

    @classmethod
    def cut_and_save(
            cls,
            video: Video,
            output_path: str,
            start: int,
            end: Optional[int] = None,
            duration: Optional[int] = None):
        """
        Arguments are made in seconds, so you might need to convert for now.
        Will fix in the future to be in minutes, hours, etc.

        If both end and duration are given, the function will default to duration.

        ffmpeg.trim(stream, **kwargs)
        Trim the input so that the output contains one continuous subpart of the input.

        Parameters
        start – Specify the time of the start of the kept section
        end – Specify the time of the first frame that will be dropped
        start_pts – This is the same as start, except this option sets the start timestamp in timebase units
        end_pts – This is the same as end, except this option sets the end timestamp in timebase units
        duration – The maximum duration of the output in seconds.
        start_frame – The number of the first frame that should be passed to the output.
        end_frame – The number of the first frame that should be dropped.
        """
        in1 = ffmpeg.input(str(video.filepath))

        if not end and not duration:
            # args not given
            trimmed = ffmpeg.trim(in1, start=start).setpts('PTS-STARTPTS')
        if all([end, duration]) or duration:
            # duration is given so takes priority
            trimmed = ffmpeg.trim(in1, start=start, end=start + duration).setpts('PTS-STARTPTS')
        else:
            trimmed = ffmpeg.trim(in1, start=start, end=end).setpts('PTS-STARTPTS')

        out = ffmpeg.output(trimmed, output_path)
        out.run()
