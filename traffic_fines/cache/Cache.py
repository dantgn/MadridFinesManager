"""
This module contains the classes responsible for managing a cache system and its functionality
"""

from pathlib import Path
from datetime import datetime

class CacheError(Exception):
    """Cache module exception"""
    pass

CACHE_DIR = Path.home() / ".my_cache"

class Cache:
    """
    Class that manages a cache system to easily store, delete and check data within the cache
    """

    def __init__(self, app_name: str, obsolescence: int, cache_dir=CACHE_DIR):
        """
        Initializes the Cache class
        :param app_name: The name of the folder within the base directory where the cache will be stored
        :param obsolescence: THe number of days the data within the cache is considered valid as int
        :param cache_dir: The base Directory where the cache will be stored, by default will be Path.home() / ".my_cache"
        """
        # params validation
        if not app_name:
                raise CacheError("app_name cannot be empty")
        if not obsolescence:
            raise CacheError("obsolescence cannot be empty")

        self.__app_name = app_name
        self.__obsolescence = obsolescence
        self.__cache_dir = Cache.create_cache_dir(cache_dir, app_name)

    @property
    def app_name(self) -> str:
        return self.__app_name
    @property
    def obsolescence(self) -> int:
        return self.__obsolescence
    @property
    def cache_dir(self) -> Path:
        return self.__cache_dir

    @staticmethod
    def create_cache_dir(cache_dir: Path, app_name: str) -> Path:
        """
        Creates the cache directory for the cache app
        :param cache_dir: Directory where the cache will be created
        :param app_name: Name that will be used for the directory
        :return:The Path of the created directory
        """
        folder = Path(cache_dir / app_name)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def set(self, name: str, data: str) -> None:
        """
        Sets a new value in the cache at a file with the given name
        :param name: The name of the cached file as String
        :param data: The data we want to store in the cache
        :return: None
        """
        file = Path(self.cache_dir / name)
        file.write_text(data)

    def exists(self, name: str) -> bool:
        """
        Checks if a cached file exists
        :param name: The Name of the cached file as String
        :return: True if exists, False otherwise
        """
        file = Path(self.cache_dir / name)
        return file.exists()

    def load(self, name: str) -> str:
        """
        Loads the content of a cached file
        :param name: The name of the cached file as String
        :return: The content of the cached file as String
        """
        file = Path(self.cache_dir / name)
        try:
            return file.read_text()
        except FileNotFoundError:
            raise CacheError(f"Cache {name} does not exist")

    def how_old(self, name: str) -> float:
        """
        Returns the age of a cached file in milliseconds
        :param name: The name of the cached file as String
        :return: Age of the file in milliseconds
        """
        file = Path(self.cache_dir / name)
        # Get the creation time with
        created_at = file.stat().st_ctime
        # Convert to datetime
        created_at_datetime = datetime.fromtimestamp(created_at)
        # Calculate age in milliseconds
        age = (datetime.now() - created_at_datetime).total_seconds() * 1000
        return age

    def is_valid(self, name: str) -> bool:
        """
        Checks if a cached file is valid or has reached the expiration time
        :param name: the name of the cached file as String
        :return: True if valid, False otherwise
        """
        # convert obsolescence days in milliseconds
        obsolescence_in_ms = self.obsolescence * 24 * 60 * 60 * 1000
        return self.how_old(name) <= obsolescence_in_ms

    def delete(self, name: str) -> None:
        """
        Deletes a cached file by name
        :param name: The name of the file to delete as String
        :return: None
        """
        file = Path(self.cache_dir / name)
        if file.exists():
            file.unlink()

    def clear(self) -> None:
        """
        Deletes all files in the cache directory
        :return: None
        """
        folder = Path(self.cache_dir)
        for file in folder.iterdir():
            if file.is_file():
                file.unlink()
