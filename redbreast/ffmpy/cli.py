from contextlib import contextmanager

import typer

from . import api

app = typer.Typer()


@contextmanager
def _handle_errors():
    try:
        yield  # allow code inside the "with" statement to run
    except Exception as e:
        match e:
            case FileNotFoundError():
                typer.secho(f"File not found: {e}", fg=typer.colors.RED)
            case api.FfmpegError():
                typer.secho(f"ffmpeg gave an error: {e}", fg=typer.colors.RED)
            case _:
                typer.secho(f"{e.__class__.__name__}: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command(help="Create a timelapse (sped up) video from a very long normal-speed video.")
def timelapse(
    input_file: str = typer.Option(
        ...,  # no default
        "--input-file",
        "-i",
    ),
    step: int = typer.Option(
        10,
        "--step",
        "-s",
        min=2,
        help="Every sth frame will be sampled from the input video.",
    ),
    input_fps: int = typer.Option(
        ...,
        "--input-fps",
        "-ifps",
        help="FPS of the input video file",
    ),
    output_fps: int = typer.Option(
        60,
        "--output-fps",
        "-ofps",
        help="Desired FPS of the output video file",
    ),
):
    with _handle_errors():
        output_file = api.create_timelapse(
            input_video=input_file,
            step=step,
            input_fps=input_fps,
            output_fps=output_fps,
        )
    typer.secho(
        f"Created file: {output_file}",
        fg=typer.colors.GREEN,
    )


@app.command(name="to-mp4")
def to_mp4(
    input_file: str = typer.Option(
        ...,
        "--input-file",
        "-i",
    ),
):
    with _handle_errors():
        output_file = api.to_mp4(input_file)
    typer.secho(f"Created file: {output_file}", fg=typer.colors.GREEN)


@app.command(help="Hello, world!")
def hello(
    name: str = typer.Option(
        "World",
        help="Name of the person to greet",
    )
):
    typer.secho(
        f"Hello, {name}!",
        fg=typer.colors.GREEN,
        bg=typer.colors.RED,
    )
