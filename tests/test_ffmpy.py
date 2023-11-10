from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from redbreast.ffmpy import cli
from redbreast.ffmpy.api import FfmpegError

runner = CliRunner()


@pytest.mark.parametrize(
    "func, cmd",
    [
        ("redbreast.ffmpy.cli.api.to_mp4", "to-mp4 -i /foo/bar"),
        ("redbreast.ffmpy.cli.api.create_timelapse", "timelapse -i /foo/bar -ifps 30 -ofps 60"),
    ],
)
@pytest.mark.parametrize(
    "exception, expected_stdout",
    [
        (FileNotFoundError("some/file"), "File not found: some/file"),
        (FfmpegError("arghh"), "ffmpeg gave an error: arghh"),
        (Exception("HELP"), "Exception: HELP"),
    ],
)
def test_cli_errors(exception, expected_stdout, func, cmd):
    with patch(func) as mock:
        mock.side_effect = exception
        result = runner.invoke(cli.app, cmd.split())
        assert result.stdout.startswith(expected_stdout)
        assert result.exit_code == 1


@pytest.mark.parametrize(
    "func, cmd",
    [
        ("redbreast.ffmpy.cli.api.to_mp4", "to-mp4 -i /foo/bar"),
        ("redbreast.ffmpy.cli.api.create_timelapse", "timelapse -i /foo/bar -ifps 30 -ofps 60"),
    ],
)
def test_cli_no_errors(func, cmd):
    with patch(func) as mock:
        mock.return_value = "some/file.mp4"
        result = runner.invoke(cli.app, cmd.split())
        assert result.exit_code == 0
