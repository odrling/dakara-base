"""Directory helper module.

This module gives application name and project name:

>>> APP_NAME
... "dakara"
>>> PROJECT_NAME
... "DakaraProject"

It also gives an evolved version of `appdirs.AppDirs` that returns `pathlib.Path`
objects:

>>> type(directories.user_config_dir)
... pathlib.Path
"""
from pathlib import Path

from platformdirs import PlatformDirs, PlatformDirsABC

APP_NAME = "dakara"
PROJECT_NAME = "DakaraProject"


class AppDirsPath:
    """AppDirs class that returns `pathlib.Path` objects."""

    def __init__(self, appdirs: PlatformDirsABC):
        self.appdirs = appdirs

    @property
    def site_config_dir(self):
        return Path(self.appdirs.site_config_dir)

    @property
    def site_data_dir(self):
        return Path(self.appdirs.site_data_dir)

    @property
    def user_cache_dir(self):
        return Path(self.appdirs.user_cache_dir)

    @property
    def user_config_dir(self):
        return Path(self.appdirs.user_config_dir)

    @property
    def user_data_dir(self):
        return Path(self.appdirs.user_data_dir)

    @property
    def user_documents_dir(self):
        return Path(self.appdirs.user_documents_dir)

    @property
    def user_log_dir(self):
        return Path(self.appdirs.user_log_dir)

    @property
    def user_runtime_dir(self):
        return Path(self.appdirs.user_runtime_dir)

    @property
    def user_state_dir(self):
        return Path(self.appdirs.user_state_dir)


directories = AppDirsPath(PlatformDirs(APP_NAME, PROJECT_NAME, roaming=True))
