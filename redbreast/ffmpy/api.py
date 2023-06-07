import shlex
import subprocess
from pathlib import Path


class FfmpegError(Exception):
    pass


def _resolve_file(path: str) -> Path:
    path = Path(path).resolve()
    if not (path.exists() and path.is_file()):
        raise FileNotFoundError(path.as_posix())
    return path


def _run_ffmpeg(cmd: str):
    """Unpack command into subprocess. Handle errors."""
    process = subprocess.run(shlex.split(cmd))
    if process.returncode:
        raise FfmpegError(f"{process.stderr}")


def create_timelapse(
    input_video: str,  # absolute path to the input video
    step,  # every step-th frame will be sampled from the input video
    input_fps,  # FPS of the input video
    output_fps=60,  # FPS of the output video
) -> str:
    """
    Create a timelapse (sped up) video from a really long normal speed video.
    """
    input_video = _resolve_file(input_video)
    output_filename = input_video.stem + "_timelapse" + input_video.suffix
    output_video = input_video.parent / output_filename
    cmd = (
        f"ffmpeg"
        f" -an"  # ignore input file audio
        f" -i {input_video.as_posix()}"
        f" -vf framestep={step},"  # sample the input video every 'framestep' frames
        f"setpts=N/{input_fps}/TB"  # space the frames at the INPUT video FPS
        f" -r {output_fps}"  # specify output video FPS again?
        f" -y"  # force overwrite
        f" {output_video.as_posix()}"
    )
    _run_ffmpeg(cmd)
    return output_video.as_posix()


def to_mp4(input_video: str) -> str:
    """Not sure why I wrote a function just for this. Apparently it was important enough though."""
    input_video = _resolve_file(input_video)
    output_video = input_video.parent / (input_video.stem + ".mp4")
    cmd = (
        "ffmpeg"
        f" -i {input_video.as_posix()}"
        f" -vcodec copy"
        f" -y "  # force overwrite
        f" {output_video.as_posix()}"
    )
    _run_ffmpeg(cmd)
    return output_video.as_posix()
