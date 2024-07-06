import datetime
from typing import Optional

import typer

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn

from backend.classes import VideoEditor
from backend.funcs import pull_from_directory

console = Console()
app = typer.Typer(no_args_is_help=True)


@app.command(short_help="stiches a video together")
def add(base_video_index: int, add_video_index: int, output_name: Optional[str] = None):
    videos = pull_from_directory()
    v1 = videos[base_video_index]
    v2 = videos[add_video_index]

    if output_name:
        if output_name[-1:-4] != ".mp4":
            raise ValueError(f"output name {output_name} is missing the '.mp4' extension!")
    if not output_name:
        output_name = f"COMBINED - {str(datetime.date.today())} - {v1.filename}-{v2.filename}.mp4"
    # We can change this in the config later on if we want to make this configurable
    export_path = f"{v1.folder_path}/{output_name}"

    VideoEditor.join_and_save(v1, v2, export_path)
    typer.echo(f"[red]Complete! Combined {v2.filename} to the end of {v2.filename}")


@app.command(short_help="trims a video")
def cut(
        video_index: int,
        start: int,
        end: Optional[int] = None,
        duration: Optional[int] = None,
        output_name: Optional[str] = None
):
    videos = pull_from_directory()
    v1 = videos[video_index]

    if output_name:
        if output_name[-1:-4] != ".mp4":
            raise ValueError(f"output name {output_name} is missing the '.mp4' extension!")
    if not output_name:
        output_name = f"Trimmed - {str(datetime.date.today())} - {v1.filename} - from {start}.mp4"
    # We can change this in the config later on if we want to make this configurable
    export_path = f"{v1.folder_path}/{output_name}"

    VideoEditor.cut_and_save(v1, export_path, start, end, duration)

    typer.echo(f"Complete!")
    typer.echo(f"Trimmed {v1.filename}: (start: {start}, end: {end}, duration: {duration})")
    typer.echo(f"Saved to {export_path}")


@app.command(short_help="shows video list")
def show():
    videos = pull_from_directory()

    table = Table(title="Available Videos")
    table.add_column("#")
    table.add_column("filename")
    table.add_column("full-path")
    table.add_column("meta")

    for idx, video in enumerate(videos):
        table.add_row(f"{idx}", video.filename, video.folder_path, video.meta)

    console.log(table)


if __name__ == "__main__":
    app()
