import json
import math
from datetime import datetime
from functools import lru_cache
from typing import Optional

import ffmpeg
import pandas as pd
from dirlin import Path, Folder


class Video:
    def __init__(self, file_path: Path, *, initiate_metadata: bool = False):
        """
        An object representing a Video. Holds information regarding the video file.

        Attributes:
            - filepath: the full path, we use this as arguments for ffmpeg functions
            - filename: the name of the video file (i.e. example.mp4)
            - stem: name of the video without the extension (i.e. example)
            - folder_path: the parent folder path (i.e. main_directory/*)
            - meta: holds data regarding the video file

        :param file_path: the pathlib.Path file path to the Video
        :param initiate_metadata: initiate metadata flag, determines whether to load metadata from videos
        """
        self.filename = str(file_path.name)
        self.stem = str(file_path.stem)
        self.folder_path = str(file_path.parent)
        self._filepath = file_path

        # separated process in order to save time
        self.meta = self.get_metadata()

    @property
    def filepath(self):
        """
        Full path of the video file. Includes the parent and the filename. Used for ffmpeg functions.
        """
        return str(self._filepath)

    @property
    def size(self):
        """
        Size in mb of the file
        """
        return json.loads(self.meta)["size"]

    @property
    def date_last_opened(self):
        """
        date the file was last opened
        """
        return json.loads(self.meta)["last_opened"]

    @property
    def date_last_modified(self):
        """
        date the file was last modified
        """
        return json.loads(self.meta)["last_modified"]

    @property
    def date_created(self):
        """
        date the file was created
        """
        return json.loads(self.meta)["created"]

    @property
    def duration(self):
        """
        duration of the video
        """
        return json.loads(self.meta)["duration"]

    @property
    def frames(self):
        """
        number of frames
        """
        return json.loads(self.meta)["frames"]

    @property
    def resolution(self):
        """
        resolution of the video

        """
        return json.loads(self.meta)["resolution"]

    def __repr__(self):
        return f"filename: {self.filename}: {self.meta}"

    def get_metadata(self):
        # Creation of the Metadata
        _size = f"{round(self._filepath.stat().st_size * 0.000001, 2)} MB"
        _last_opened = f"{datetime.fromtimestamp(self._filepath.stat().st_atime)}"
        _last_modified = f"{datetime.fromtimestamp(self._filepath.stat().st_mtime)}"
        try:
            _created = f"{datetime.fromtimestamp(self._filepath.stat().st_birthtime)}"
        except AttributeError:
            _created = "Unknown"

        # metadata from ffmpeg.probe
        try:
            _probe = ffmpeg.probe(str(self._filepath))
            _vs = next((stream for stream in _probe["streams"] if stream['codec_type'] == 'video'), None)
        except Exception as e:
            print(e)
            _vs = dict()
            _vs['duration'] = 60
            _vs['avg_frame_rate'] = '30'
            _vs['width'] = 0
            _vs['height'] = 0

        _duration = float(_vs['duration'])
        _fps = eval(_vs["avg_frame_rate"])
        _total_frames = int(_duration * _fps)
        _resolution = f"{_vs['width']}x{_vs['height']}"

        _meta = {
            "size": _size,
            "last_opened": _last_opened,
            "last_modified": _last_modified,
            "created": _created,
            "duration": _duration / 60,
            "frames": _total_frames,
            "resolution": _resolution
        }
        return json.dumps(_meta)


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
            trimmed_vid = in1.video.trim(start=start).setpts('PTS-STARTPTS')
            trimmed_aud = in1.audio.filter_('atrim', start=start).filter_('asetpts', 'PTS-STARTPTS')
        elif all([end, duration]) or duration:
            # duration is given so takes priority
            trimmed_vid = in1.video.trim(start=start, end=start + duration).setpts('PTS-STARTPTS')
            trimmed_aud = (
                in1.audio
                .filter_('atrim', start=start, end=start + duration)
                .filter_('asetpts', 'PTS-STARTPTS')
            )
        else:
            trimmed_vid = in1.video.trim(start=start, end=end).setpts('PTS-STARTPTS')
            trimmed_aud = (
                in1.audio
                .filter_('atrim', start=start, end=end)
                .filter_('asetpts', 'PTS-STARTPTS')
            )

        joined = ffmpeg.concat(trimmed_vid, trimmed_aud, v=1, a=1).node
        out = ffmpeg.output(joined[0], joined[1], output_path)
        out.run()

    @classmethod
    def generate_thumbnail_sheet(
            cls,
            video: Video,
            output_path: str,
            columns: Optional[int] = 5,
            rows: Optional[int] = 4
    ):
        thumbnail_width = 320
        thumbnail_length = 240

        # frames between each snapshot
        frames = max(1, math.floor(video.frames / (columns * rows)))
        metadata_text = f"Filename: {video.filename}, File Size: {video.size}"

        in1 = ffmpeg.input(video.filepath)
        out = (
            in1
            .filter('select', fr'not(mod(n, {frames}))')
            .filter('scale', thumbnail_width, thumbnail_length)
            .filter('drawtext', text='%{pts:hms}', x=10, y=10, fontsize=24, fontcolor='white')
            .filter('tile', f'{columns}x{rows}')
            .output(output_path, vsync='vfr', vframes=1)
        )
        out.run()


class ApplicationConfig:
    @classmethod
    def return_current_directory(cls):
        """
        Function for returning the current working directory

        """
        get_path = str(Path(__file__).parent.parent / "app_config.json")

        with open(get_path, "r") as f:
            config_options = json.loads(f.read())
        if config_options["folder"] == "default":
            path = Path(__file__).parent.parent / "files"
        else:
            path = config_options["folder"]
        return path

    @classmethod
    def change_current_directory(cls, cwd: str | Path) -> bool:
        """
        Function for changing the current working directory and writes in the app_config JSON file
        :param cwd: the working directory you want to update to. Can set to 'default' to change it back
        :return: return True when complete
        """
        get_path = str(Path(__file__).parent.parent / "app_config.json")

        try:
            if isinstance(cwd, str) and cwd != "default":
                cwd = Path(cwd)
            if cwd != "default":
                assert cwd.exists()
        except AssertionError:
            raise AssertionError(f"The directory {cwd} does not exist.")

        with open(get_path, "r+") as f:
            config_options = json.load(f)
            config_options['folder'] = str(cwd)
            f.seek(0)
            json.dump(config_options, f, indent=4)
            f.truncate()
        return True

    @classmethod
    @lru_cache()
    def pull_from_directory(cls, file_ext=".mp4", *index_file_args, **index_file_kw) -> list[Video]:
        """
        Pulls from the app_config.json file in the root of the app, to determine which folder to
        pull the files from. The function itself returns a Folder object. If missing, creates a folder

        :return:
        """
        get_path = str(Path(__file__).parent.parent / "app_config.json")

        with open(get_path, "r") as j_file:
            config_options = json.loads(j_file.read())

        if config_options["folder"] == "default":
            default_path = Path(__file__).parent.parent / "files"
            if not default_path.exists():
                default_path.mkdir(parents=True, exist_ok=True)
            folder_path = Folder(default_path)
        else:
            folder_path = Folder(config_options["folder"])
        videos = [Video(v) for v in folder_path.index_files(file_ext=file_ext, *index_file_args, **index_file_kw)]
        return videos

    @classmethod
    def as_dataframe(cls, *index_file_args, **index_file_kw) -> pd.DataFrame:
        """
        returns the video list as a dataframe. this allows the sorting of the table in the main application.

        :param file_ext: the extension we are searching for in the folders
        :param index_file_args: arguments for the index_files function
        :param index_file_kw: keyword arguments for the index_files function
        :return: dataframe representation of the file and the metadata
        """
        videos = cls.pull_from_directory(*index_file_args, **index_file_kw)

        df_mapping = {
            "idx": [],
            "filename": [],
            "folder_path": [],
            "size": [],
            "date_created": [],
            "date_modified": [],
            "date_accessed": [],
            "duration": [],
            "resolution": []
        }
        for idx, video in enumerate(videos):
            df_mapping["idx"].append(idx)
            df_mapping["filename"].append(video.filename)
            df_mapping["folder_path"].append(video.folder_path)
            df_mapping["size"].append(video.size)
            df_mapping["date_created"].append(video.date_created)
            df_mapping["date_modified"].append(video.date_last_modified)
            df_mapping["date_accessed"].append(video.date_last_opened)
            df_mapping["duration"].append(video.duration)
            df_mapping["resolution"].append(video.resolution)

        df = pd.DataFrame.from_dict(df_mapping)
        return df
