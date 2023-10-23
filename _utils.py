import os
import sys
import subprocess


class Downloads():
    def __init__(self):
        self._path_downloads = None
        self.set_path()


    def set_path(self, path: str=None):
        """Set path of downloads directory.

        Syntax:
            `Vimeo.set_path(path)`

        Args:
            e.g. `path="C:\\\\Users\\\\User\\\\Desktop"`.
        """
        if path == None:
            if os.name == "nt":
                user_env = os.getenv("USERPROFILE")
                self.path_downloads = os.path.join(user_env, "Downloads")
            else:
                self.path_downloads = os.getcwd() + "\downloads"

        else:
            try:
                if os.path.exists(path) and os.path.isdir(path):
                    self.path_downloads = path
                else:
                    raise ValueError
            except:
                print("Error: Bad Download Path Selected")
                sys.exit(2)


    def check_path(self):
        """Return path of downloads directory.

        Syntax:
            `Vimeo.check_path()`
        """
        return os.path.abspath(self.path_downloads)
    
    
    @property
    def path_downloads(self):
        return self._path_downloads
    
    @path_downloads.setter
    def path_downloads(self, value):
        if os.path.abspath(value) or os.path.realpath(value):
            self._path_downloads = os.path.relpath(value)


def _check_ffmpeg() -> None:
    """Uses subprocess to find if `FFmpeg` is available in `PATH`.
    """
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError:
        print("Error: FFmpeg Is Not in the PATH")
        sys.exit(4)