# This class downloads a zip with the AI models from Github Releases and
# unzips it to the .models/ folder.

import os
from typing import Callable
import requests
import zipfile
from tempfile import gettempdir
from os.path import join
from urllib.parse import urlparse

release_tag = "v0.0.0"

models_filename = "models.zip"

models_zip_url = f"https://github.com/jhm-ciberman/phantom-desktop/releases/download/{release_tag}/{models_filename}"

local_models_folder = join(os.getcwd(), "models")


class ModelsDownloader:
    """
    Downloads a zip with the AI models from Github Releases and unzips it to the .models/ folder.
    """

    on_download_progress: Callable[[int, int], None] = None
    """
    Callback function to be called when the download progress changes.
    It receives the current and total bytes downloaded.
    """

    on_extract_progress: Callable[[int, int], None] = None
    """
    Callback function to be called when the unzip progress changes.
    It receives the current and total files unzipped.
    """

    _release_tag_file = f"{local_models_folder}/release_tag.txt"

    def __init__(
            self, on_download_progress: Callable[[int, int], None] = None,
            on_unzip_progress: Callable[[int, int], None] = None):
        """
        Initializes a new instance of the ModelsDownloader class.

        Args:
            on_download_progress (Callable[[int, int], None], optional): Callback function to be called when
                the download progress changes. It receives the current and total bytes downloaded. Defaults to None.
            on_extract_progress (Callable[[int, int], None], optional): Callback function to be called when
                the unzip progress changes. It receives the current and total files unzipped. Defaults to None.
        """
        self.on_download_progress = on_download_progress
        self.on_extract_progress = on_unzip_progress

    def _download_file(self, url: str) -> str:
        """
        Downloads a file from the given url and returns the path to the downloaded file.
        The file is downloaded in a temporary folder.
        """
        file_name = urlparse(url).path.split("/")[-1]
        local_filename = join(gettempdir(), file_name)
        print(f"Downloading {url} to {local_filename}")
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            raise Exception(f"Error downloading {url}. Status code: {r.status_code}")
        content_length = r.headers.get('content-length')
        total_length = int(content_length) if content_length is not None else None
        with open(local_filename, 'wb') as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if self.on_download_progress:
                        self.on_download_progress(downloaded, total_length)
        return local_filename

    def _unzip_file(self, file_path: str):
        """
        Unzips the given file to the .models/ folder. The file is deleted after unzipping.
        """
        print(f"Unzipping {file_path} to {local_models_folder}")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            total_files = len(zip_ref.namelist())
            extracted = 0
            for file in zip_ref.namelist():
                zip_ref.extract(file, local_models_folder)
                extracted += 1
                if self.on_extract_progress:
                    self.on_extract_progress(extracted, total_files)
        os.remove(file_path)

    def _write_release_tag(self):
        """
        Writes the release tag to the .models/ folder.
        """
        with open(self._release_tag_file, "w") as f:
            f.write(release_tag)

    def _read_release_tag(self) -> str:
        """
        Reads the release tag from the .models/ folder. If the file doesn't exist, returns an empty string.
        """
        if os.path.exists(self._release_tag_file):
            with open(self._release_tag_file, "r") as f:
                return f.read()
        return ""

    def models_are_updated(self) -> bool:
        """
        Checks if the models are updated by comparing the release tag in
        the .models/ folder with the release tag in this file.
        """
        return self._read_release_tag() == release_tag

    def download_models(self) -> bool:
        """
        Downloads the models zip from Github Releases if required.
        """
        if not self.models_are_updated():
            file_path = self._download_file(models_zip_url)
            self._unzip_file(file_path)
            self._write_release_tag()
            return True
        return False
