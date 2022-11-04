import shutil
import subprocess
from pathlib import Path


def cleanup():
    for folder in [Path(__file__).parent / "redbreast.egg-info", Path(__file__).parent / "dist"]:
        if folder.exists():
            shutil.rmtree(folder)


cleanup()
subprocess.run("python -m build".split())
subprocess.run("twine upload dist/*".split())
cleanup()
