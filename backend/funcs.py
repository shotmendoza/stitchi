import json
from functools import lru_cache

from dirlin import Folder, Path

from backend.classes import Video


@lru_cache()
def pull_from_directory(file_ext=".mp4", *index_file_args, **index_file_kw) -> list[Video]:
    """
    Pulls from the app_config.json file in the root of the app, to determine which folder to
    pull the files from. The function itself returns a Folder object.

    :return:
    """
    get_path = str(Path(__file__).parent.parent / "app_config.json")

    with open(get_path, "r") as j_file:
        config_options = json.loads(j_file.read())

    if config_options["folder"] == "default":
        folder_path = Folder(Path(__file__).parent.parent / "files")
    else:
        folder_path = Folder(config_options["folder"])
    videos = [Video(v) for v in folder_path.index_files(file_ext=file_ext, *index_file_args, **index_file_kw)]
    return videos
