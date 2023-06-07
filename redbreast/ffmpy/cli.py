import typer

from . import api

app = typer.Typer()


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
