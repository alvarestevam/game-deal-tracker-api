import pytest
from app.services.sync_service import _sanitize_steam_image_url, _sanitize_gamesplanet_image_url

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

def test_sanitize_gamesplanet_image_url_dimension_prefix():
    url = "https://gpstatic.com/acache/77/96/1/us/t280x115-b9ec8af8fbfd66e604a4d23e0b49028b.jpg"
    expected = "https://gpstatic.com/acache/77/96/1/us/packshot-b9ec8af8fbfd66e604a4d23e0b49028b.jpg"
    assert _sanitize_gamesplanet_image_url(url) == expected

def test_sanitize_gamesplanet_image_url_different_dimension():
    url = "https://us.gamesplanet.com/acache/12/34/5/us/t620x300-abcdef.jpg"
    expected = "https://us.gamesplanet.com/acache/12/34/5/us/packshot-abcdef.jpg"
    assert _sanitize_gamesplanet_image_url(url) == expected

def test_sanitize_gamesplanet_image_url_suffixes():
    url = "https://us.gamesplanet.com/images/game_small.jpg"
    expected = "https://us.gamesplanet.com/images/game.jpg"
    assert _sanitize_gamesplanet_image_url(url) == expected

def test_sanitize_gamesplanet_image_url_thumb_suffix():
    url = "https://gpstatic.com/covers/game_thumb.jpg"
    expected = "https://gpstatic.com/covers/game.jpg"
    assert _sanitize_gamesplanet_image_url(url) == expected

def test_sanitize_gamesplanet_image_url_no_match():
    url = "https://us.gamesplanet.com/acache/77/96/1/us/packshot-b9ec8af8fbfd66e604a4d23e0b49028b.jpg"
    assert _sanitize_gamesplanet_image_url(url) == url

def test_sanitize_gamesplanet_image_url_non_gamesplanet():
    url = "https://m.media-amazon.com/images/M/some_image_small.jpg"
    assert _sanitize_gamesplanet_image_url(url) == url
