import subprocess
from pathlib import Path
import shlex


def create_timelapse(
    input_video: str,  # absolute path to the input video
    step,  # every step-th frame will be sampled from the input video
    input_fps,  # FPS of the input video
    output_fps=60,  # FPS of the output video
) -> str:
    """
    Create a timelapse (sped up) video from a really long normal speed video.
    """
    input_video = Path(input_video)
    output_filename = input_video.stem + "_timelapse" + input_video.suffix
    assert input_video.exists()
    print(f"Input file: {input_video.as_posix()}")

    output_file = input_video.parent / output_filename
    print(f"Output file: {output_file.as_posix()}")
    cmd = (
        f"ffmpeg"
        f" -an"  # ignore input file audio
        f" -i {input_video.as_posix()}"
        f" -vf framestep={step},"  # sample the input video every 'framestep' frames
        f"setpts=N/{input_fps}/TB"  # space the frames at the INPUT video FPS
        f" -r {output_fps}"  # specify output video FPS again?
        f" -y"  # force overwrite
        f" {output_file.as_posix()}"
    )
    print(f"cmd: {cmd}")
    process = subprocess.run(shlex.split(cmd))
    if process.returncode:
        raise Exception(f"Error: {process.stderr}")
    return output_file.as_posix()
