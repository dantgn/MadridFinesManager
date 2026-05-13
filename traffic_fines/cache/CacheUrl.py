"""
This module contains the class responsible for managing a cache system specific for Web Urls
"""
import requests
from .Cache import Cache, CacheError
import hashlib

class CacheUrl(Cache):
    """
    Class responsible for managing a cache system specific for Web Urls
    Inherits from Cache class
    """
    def get(self, url: str) -> str:
        """
        Gets the content of a cached url.
        In case of an url not stored yet in cache, it gets the content from the network
        and stores the content in the cache
        :param url: Url to get from the cache as String
        :return: the content of the url as String
        """
        url_key = CacheUrl.url_hash(url)
        if self.exists(url):
            if self.is_valid(url):
                return self.load(url)
            else:
                self.delete(url)

        response = requests.get(url)
        if response.status_code != 200:
            raise CacheError(f"url: {url} returned status code {response.status_code}")
        content = response.text
        self.set(url_key, content)

        return content

    @staticmethod
    def url_hash(url: str) -> str:
        """
        Generate a hash string for a given url
        :param url: The url to convert to hash
        :return: The hash of the url as String

        Example:
        ---------
        >>> CacheUrl.url_hash("https://www.python.org")
        'c137682bbb0946674f25d1d4bd9e07a0'

        >>> CacheUrl.url_hash("")
        Traceback (most recent call last):
        ...
        traffic_fines.cache.Cache.CacheError: Please provide a valid url
        """
        if not url:
            raise CacheError("Please provide a valid url")

        url_hashed = hashlib.md5(url.encode('utf-8')).hexdigest()
        return url_hashed

    def exists(self, url: str) -> bool:
        """
        Checks if a url has its content cached
        :param url: The url to check if exists as String
        :return: True if exists, False otherwise
        """
        url_key = self.url_hash(url)
        return super().exists(url_key)

    def load(self, url: str) -> str:
        """
        Loads the content of a cached url
        :param url: The cached url as String
        :return: The content of the cached url as String
        """
        url_key = self.url_hash(url)
        return super().load(url_key)

    def how_old(self, url: str) -> float:
        """
        Returns the age of a url cached. in milliseconds
        :param url: The url to check as String
        :return: Age of the cached url in milliseconds
        """
        url_key = self.url_hash(url)
        return super().how_old(url_key)

    def delete(self, url: str) -> None:
        """
        Deletes a url from the cache
        :param url: The url to delete from the cache as String
        :return: None
        """
        url_key = self.url_hash(url)
        super().delete(url_key)

