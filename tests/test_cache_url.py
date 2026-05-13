import datetime
from pathlib import Path
import doctest
import pytest
from traffic_fines.cache import CacheUrl, CacheError

# create a mocked hash key, hash_url has already its own test
MOCKED_HASH_KEY = "38634350ed2d6e54f5f9d409c77b384d"

def test_url_hash_doctest():
    doctest.run_docstring_examples(CacheUrl.url_hash, globals(), verbose=True)

@pytest.mark.parametrize(
    "url, data, is_cached, is_valid", [
        ("https://docs.python.org", "Some information", True, True),
        ("https://docs.python.org", "Some information", True, False),
        ("https://docs.python.org", "Some information", False, True),
    ]
)
def test_get(monkeypatch, requests_mock, tmp_path, url, data, is_cached, is_valid):
    # Prepare an existing cached file
    cache_url = CacheUrl("test_app", 10, cache_dir=tmp_path)

    if not is_valid:
        # monkey patch the creation of the cached file to make obsolescence fail and make remove the invalid cached file
        may_first = datetime.datetime(year=2024, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        class FakeStat:
            def __init__(self, st_ctime):
                self.st_ctime = st_ctime
        def fake_file_creation_date(self):
            return FakeStat(may_first.timestamp())
        monkeypatch.setattr(Path, "stat", fake_file_creation_date)

    if is_cached:
        url_hashed = cache_url.url_hash(url)
        cache_url.set(url_hashed, data)

    if not is_valid or not is_cached:
        # Mock the http response
        requests_mock.get(url, text=data)

    content = cache_url.get(url)
    assert content == data

@pytest.mark.parametrize(
    "url, data", [
        ("https://docs.python.org", "404 Not Found"),
    ]
)
def test_get_errors(requests_mock, tmp_path, url, data):
    with pytest.raises(CacheError):
        cache_url = CacheUrl("test_app", 10, cache_dir=tmp_path)
        # Mock the http response
        requests_mock.get(url, text=data, status_code=404)
        cache_url.get(url)

@pytest.mark.parametrize(
    "name, create_file, expected", [
        ("www.python.org", True, True)
    ]
)
def test_exists(monkeypatch, tmp_path, name, create_file, expected):
    monkey_patch_url_hash(monkeypatch)
    cache_url = CacheUrl("test_app", 10, cache_dir=tmp_path)

    if create_file:
        # simulate we already had the file cached
        file_path = cache_url.cache_dir / MOCKED_HASH_KEY
        file_path.touch()

    assert cache_url.exists(name) is expected

@pytest.mark.parametrize(
    "name, data", [
        ("www.python.org", "Some information"),
    ]
)
def test_load(monkeypatch, tmp_path, name, data):
    monkey_patch_url_hash(monkeypatch)
    cache_url = CacheUrl("test_app", 10, cache_dir=tmp_path)
    # prepare data for testing with set
    cache_url.set(MOCKED_HASH_KEY, data)

    assert cache_url.load(name) == data

@pytest.mark.parametrize(
    "name", [
        "www.python.org",
    ]
)
def test_load_errors(monkeypatch, tmp_path, name):
    with pytest.raises(CacheError):
        cache_url = CacheUrl("test_app", 10, cache_dir=tmp_path)
        # File cache for the specific name does not exist
        cache_url.load(name)

@pytest.mark.parametrize(
    "name, expected", [
        ("www.python.org", False)
    ]
)
def test_delete(monkeypatch, tmp_path, name, expected):
    monkey_patch_url_hash(monkeypatch)
    cache_url = CacheUrl("test_app", 10, cache_dir=tmp_path)

    file_path = cache_url.cache_dir / MOCKED_HASH_KEY

    # create temporary fake cache file
    file_path.touch()

    cache_url.delete(name)
    assert file_path.exists() is expected

def monkey_patch_url_hash(monkeypatch):
    """
    Helper method to monkey-patch the url_hash method, since ew already have a separate test for this method,
    we can omit this and just return a mocked value for url_hash in the tests
    """
    def fake_hash(self, url):
        return MOCKED_HASH_KEY

    monkeypatch.setattr(CacheUrl, "url_hash", fake_hash)