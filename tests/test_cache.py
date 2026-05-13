import datetime
import pytest
from pathlib import Path
from traffic_fines.cache import Cache, CacheError
from freezegun import freeze_time

def test_initialize(tmp_path):
    cache = Cache(app_name="test_app", obsolescence=10, cache_dir=tmp_path)

    assert cache.app_name == "test_app"
    assert cache.obsolescence == 10
    assert cache.cache_dir == tmp_path / "test_app"

@pytest.mark.parametrize(
    "app_name,obsolescence",
    [
        (None, 10),
        ("test_app", None)
    ]
)
def test_initialize_errors(app_name, obsolescence):
    with pytest.raises(CacheError):
        Cache(app_name, obsolescence)

def test_create_cache_dir(tmp_path):
    app_name = "test_app"
    cache_dir = tmp_path
    expected_cache_dir = cache_dir / app_name
    assert expected_cache_dir.exists() is False

    Cache.create_cache_dir(cache_dir, app_name)
    assert expected_cache_dir.exists()

@pytest.mark.parametrize(
    "name, create_file, expected", [
        ("38634350ed2d6e54f5f9d409c77b384d", True, True),
        ("89f16ab7de9820bb0e24cd269c9bef93", False, False),
    ]
)
def test_exists(tmp_path, name, create_file, expected):
    cache = Cache("test_app", 10, cache_dir=tmp_path)
    file_path = cache.cache_dir / name

    if create_file:
        # simulate we already had the file cached
        file_path.touch()

    assert cache.exists(name) is expected


@pytest.mark.parametrize(
    "name, data", [
        ("38634350ed2d6e54f5f9d409c77b384d", "Some information"),
    ]
)
def test_set(tmp_path, name, data):
    cache = Cache("test_app", 10, cache_dir=tmp_path)

    cache.set(name, data)
    file = cache.cache_dir / name
    assert file.read_text() == data

@pytest.mark.parametrize(
    "name, data", [
        ("38634350ed2d6e54f5f9d409c77b384d", "Some information"),
    ]
)
def test_load(tmp_path, name, data):
    cache = Cache("test_app", 10, cache_dir=tmp_path)
    cache.set(name, data)
    assert cache.load(name) == data

@pytest.mark.parametrize(
    "name", [
        "38634350ed2d6e54f5f9d409c77b384d",
    ]
)
def test_load_errors(tmp_path, name):
    with pytest.raises(CacheError):
        cache = Cache("test_app", 10, cache_dir=tmp_path)
        # File cache for the specific name does not exist
        cache.load(name)

@pytest.mark.parametrize(
    "name", [
        "38634350ed2d6e54f5f9d409c77b384d"
    ]
)
@freeze_time("2026-05-05")
def test_how_old(monkeypatch, tmp_path, name):
    # I decided to use freezetime from freezegun library to freeze today's date as '2026-05-05'

    cache = Cache("test_app", 10, cache_dir=tmp_path)
    # create temporary fake cache file
    file_path = cache.cache_dir / name
    file_path.touch()

    # monkey patch the creation of the cached file as if it was created on May 1st 2026
    may_first = datetime.datetime(year=2026,month=5,day=1,hour=0,minute=0,second=0,microsecond=0)
    class FakeStat:
        def __init__(self, st_ctime):
            self.st_ctime = st_ctime
    def fake_file_creation_date(self):
        return FakeStat(may_first.timestamp())
    monkeypatch.setattr(Path, "stat", fake_file_creation_date)

    # age should be 4 days, which is 345600000.0 milliseconds
    assert cache.how_old(name) == 345600000.0

@pytest.mark.parametrize(
    "name", [
        "38634350ed2d6e54f5f9d409c77b384d",
    ]
)
def test_is_valid(tmp_path, name):
    # set expiration after 1 day
    cache = Cache("test_app", 10, cache_dir=tmp_path)

    # # create temporary fake cache file
    file_path = cache.cache_dir / name
    file_path.touch()

    assert cache.is_valid(name) is True

@pytest.mark.parametrize(
    "name", [
        "38634350ed2d6e54f5f9d409c77b384d",
    ]
)
def test_is_valid_errors(monkeypatch, tmp_path, name):
    cache = Cache("test_app", 1, cache_dir=tmp_path)

    # # create temporary fake cache file
    file_path = cache.cache_dir / name
    file_path.touch()

    # monkeypatch the creation of the cached file as if it was created on March 1st 2026, just some day in the past
    march_first = datetime.datetime(year=2026,month=3,day=1,hour=9,minute=0,second=0,microsecond=0)
    class FakeStat:
        def __init__(self, st_ctime):
            self.st_ctime = st_ctime
    def fake_file_creation_date(self):
        return FakeStat(march_first.timestamp())
    monkeypatch.setattr(Path, "stat", fake_file_creation_date)

    assert cache.is_valid(name) is False

@pytest.mark.parametrize(
    "name, expected", [
        ("38634350ed2d6e54f5f9d409c77b384d", False)
    ]
)
def test_delete(tmp_path, name, expected):
    cache = Cache("test_app", 10, cache_dir=tmp_path)
    file_path = cache.cache_dir / name

    # create temporary fake cache file
    file_path.touch()

    cache.delete(name)
    assert file_path.exists() is expected

@pytest.mark.parametrize(
    "create_files, expected", [
        ( True, False)
    ]
)
def test_clear(tmp_path, create_files, expected):
    cache = Cache("test_app", 10, cache_dir=tmp_path)

    if create_files:
        for file in ["38634350ed2d6e54f5f9d409c77b384d", "89f16ab7de9820bb0e24cd269c9bef93"]:
            file_path = cache.cache_dir / file
            # simulate we already had the file cached
            file_path.touch()

    cache.clear()
    assert any(Path(cache.cache_dir).iterdir()) is expected
