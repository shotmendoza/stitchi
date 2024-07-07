import json
from functools import lru_cache

from dirlin import Folder, Path

from backend.classes import Video


def return_current_directory():
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


def change_current_directory(cwd: str | Path) -> bool:
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
        default_path = Path(__file__).parent.parent / "files"
        if default_path.exists():
            folder_path = Folder(default_path)
        else:
            default_path.mkdir(parents=True, exist_ok=True)
            folder_path = Folder(default_path)
    else:
        folder_path = Folder(config_options["folder"])
    videos = [Video(v) for v in folder_path.index_files(file_ext=file_ext, *index_file_args, **index_file_kw)]
    return videos
