import datetime
import random
from typing import Optional

import typer
from rich import box
from rich.align import Align
from rich.prompt import Prompt, Confirm

from rich.console import Console
from rich.table import Table
from rich.text import Text

from stitch.backend.classes import VideoEditor, ApplicationConfig

console = Console()
app = typer.Typer(no_args_is_help=True)


@app.command(short_help="stiches a video together. takes base index, addon index, and output name")
def add(base_video_index: int, add_video_index: int, output_name: Optional[str] = None):
    videos = ApplicationConfig.pull_from_directory(recurse=True)
    v1 = videos[base_video_index]
    v2 = videos[add_video_index]

    if output_name:
        if output_name[-4:] != ".mp4":
            raise ValueError(f"output name {output_name} is missing the '.mp4' extension! ({output_name[-4:]})")
    if not output_name:
        output_name = f"COMBINED - {str(datetime.date.today())} - {v1.stem}-{v2.stem}.mp4"
    # We can change this in the config later on if we want to make this configurable
    export_path = f"{v1.folder_path}/{output_name}"

    VideoEditor.join_and_save(v1, v2, export_path)
    typer.echo(f"[red]Complete! Combined {v2.filename} to the end of {v2.filename}")


@app.command(short_help="trims a video. takes index, start (in seconds), end or duration (seconds), and outputs name.")
def trim(
        video_index: int,
        start: int,
        end: Optional[int] = None,
        duration: Optional[int] = None,
        output_name: Optional[str] = None
):
    videos = ApplicationConfig.pull_from_directory(recurse=True)
    v1 = videos[video_index]

    if output_name:
        if output_name[-4:] != ".mp4":
            raise ValueError(f"output name {output_name} is missing the '.mp4' extension!")
    if not output_name:
        output_name = f"Trimmed - {str(datetime.date.today())} - {v1.stem} - from {start}.mp4"
    # We can change this in the config later on if we want to make this configurable
    export_path = f"{v1.folder_path}/{output_name}"

    VideoEditor.cut_and_save(v1, export_path, start, end, duration)

    typer.echo(f"Complete!")
    typer.echo(f"Trimmed {v1.filename}: (start: {start}, end: {end}, duration: {duration})")
    typer.echo(f"Saved to {export_path}")


@app.command(short_help="plays the video. takes an index integer as an argument. Shuffles if left blank")
def play(video_index: int, shuffle: Optional[bool] = False):
    videos = ApplicationConfig.pull_from_directory(recurse=True)

    if shuffle:
        if len(videos) == 0:
            raise IndexError(f"There are no videos in the folder!")
        video_index = random.randint(0, len(videos) - 1)
    typer.launch(videos[video_index].filepath)

    video_text = Text(f"Opened: {videos[video_index].filename} ({video_index})", justify="center")
    video_text.stylize("bold green on white", 0, 7)
    video_text.stylize("bold red on white", 8)
    console.print(video_text, justify="center")


@app.command(
    help="shows the video list. first column is the index integer used for the app. When sorting, any space "
         "needs to be hyphenated '-'. For example, 'date-created'.")
def show(sort: Optional[list[str]] = None, ascending: Optional[bool] = True):
    videos = ApplicationConfig.as_dataframe(recurse=True)
    console.clear()

    # Table Positioning
    table = Table(title="Available Videos", box=box.HORIZONTALS, leading=True, row_styles=["steel_blue3"])
    table_centered = Align.center(table)
    table.add_column("#")
    table.add_column("filename")
    table.add_column("full path")
    table.add_column("size")
    table.add_column("date created")
    table.add_column("date modified")
    table.add_column("date accessed")
    table.add_column("duration")
    table.add_column("resolution")

    # Dataframe Configuration
    user_sort_input_mapping = {
        "#": "idx",
        "file-name": "filename",
        "full-path": "folder_path",
        "fullpath": "folder_path",
        "size": "size",
        "date-created": "date_created",
        "date-modified": "date_modified",
        "date-accessed": "date_accessed",
        "duration": "duration",
        "resolution": "resolution",
    }
    if sort:
        try:
            sort = [user_sort_input_mapping[f.lower()] for f in sort]
            videos = videos.sort_values(by=sort, ascending=ascending)
        except KeyError:
            raise KeyError(f"{sort} is not valid! Available: {videos.columns}")

    for video in videos.itertuples():
        table.add_row(
            str(video.idx),
            str(video.filename),
            str(video.folder_path),
            str(video.size),
            str(video.date_created),
            str(video.date_modified),
            str(video.date_accessed),
            str(video.duration),
            str(video.resolution)
        )
    console.log(table_centered)


@app.command(short_help="changes the directory and overwrites the JSON file")
def change_directory():
    curr_folder = ApplicationConfig.return_current_directory()

    console.print(f"[bold cyan]({curr_folder})[/bold cyan]", new_line_start=True)
    cwd = Prompt.ask(
        f"Where would you like your working directory to be?",
        default=curr_folder
    )
    if cwd != curr_folder:
        confirmed = Confirm.ask(f"Are you sure you would like to change the default directory?", default=False)
        if confirmed:
            ApplicationConfig.change_current_directory(cwd)
            console.print(f"Changed directory to [green on white]{str(cwd)}[/green on white]!")
            return
    console.print(f"[green]Directory is the same![/green]")


@app.command(short_help="generates a thumbnail contact sheet")
def thumbnail_sheet(
        video_index: int,
        output_name: Optional[str] = None,
        columns: Optional[int] = 5,
        rows: Optional[int] = 4
):
    videos = ApplicationConfig.pull_from_directory(recurse=True)
    v1 = videos[video_index]

    allowed = [".png", "jpeg", ".bmp", "tiff"]
    if output_name:
        if output_name[-4:] not in allowed:
            raise ValueError(f"output name {output_name[-1:-4]} is NOT an approved file type!")
    if not output_name:
        output_name = f"Thumbnail Sheet - {v1.stem} - {str(datetime.date.today())}.png"
    # We can change this in the config later on if we want to make this configurable
    export_path = f"{v1.folder_path}/{output_name}"
    VideoEditor.generate_thumbnail_sheet(video=v1, output_path=export_path, columns=columns, rows=rows)

    typer.echo(f"Complete!")
    typer.echo(f"Created a Thumbnail Sheet for {v1.stem}!")
    typer.echo(f"Saved to {export_path}")


if __name__ == "__main__":
    app()
