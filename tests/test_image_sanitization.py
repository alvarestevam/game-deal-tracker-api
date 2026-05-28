import pytest
from app.services.sync_service import _sanitize_steam_image_url

def test_sanitize_steam_image_url_basic():
    url = "https://cdn.akamai.steamstatic.com/steam/apps/12345/capsule_sm_120.jpg"
    expected = "https://cdn.akamai.steamstatic.com/steam/apps/12345/header.jpg"
    assert _sanitize_steam_image_url(url) == expected

def test_sanitize_steam_image_url_different_size():
    url = "https://cdn.akamai.steamstatic.com/steam/apps/12345/capsule_616x353.jpg"
    expected = "https://cdn.akamai.steamstatic.com/steam/apps/12345/header.jpg"
    assert _sanitize_steam_image_url(url) == expected

def test_sanitize_steam_image_url_with_query_params():
    url = "https://cdn.akamai.steamstatic.com/steam/apps/12345/capsule_sm_120.jpg?t=123456"
    expected = "https://cdn.akamai.steamstatic.com/steam/apps/12345/header.jpg?t=123456"
    # Note: re.sub(r"capsule_.*\.jpg", "header.jpg", url) will replace everything from capsule_ to .jpg
    # If the URL is "https://.../capsule_sm_120.jpg?t=123456", it will replace "capsule_sm_120.jpg" with "header.jpg"
    # result: "https://.../header.jpg?t=123456"
    assert _sanitize_steam_image_url(url) == expected

def test_sanitize_steam_image_url_non_steam():
    url = "https://m.media-amazon.com/images/M/some_image.jpg"
    assert _sanitize_steam_image_url(url) == url

def test_sanitize_steam_image_url_none():
    assert _sanitize_steam_image_url(None) is None

def test_sanitize_steam_image_url_empty():
    assert _sanitize_steam_image_url("") == ""

def test_sanitize_steam_image_url_generic_steam():
    url = "https://steamcdn-a.akamaihd.net/steam/apps/123/capsule_231x87.jpg"
    expected = "https://steamcdn-a.akamaihd.net/steam/apps/123/header.jpg"
    assert _sanitize_steam_image_url(url) == expected
