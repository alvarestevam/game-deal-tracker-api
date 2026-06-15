import sys
import os

# Add the current directory to sys.path to allow imports from 'app'
sys.path.append(os.getcwd())

from app.services.sync_service import _sanitize_steam_image_url
from app.utils.store_mapper import map_store, STORE_DATA

def test_steam_url_rewrite():
    test_cases = [
        # Fastly URL with hash and token
        (
            "https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/12345/HASH/header.jpg?t=123456789",
            "https://cdn.akamai.steamstatic.com/steam/apps/12345/header.jpg"
        ),
        # Simple steamstatic URL
        (
            "https://cdn.cloudflare.steamstatic.com/steam/apps/67890/header.jpg",
            "https://cdn.akamai.steamstatic.com/steam/apps/67890/header.jpg"
        ),
        # Capsule thumbnail URL
        (
            "https://cdn.cloudflare.steamstatic.com/steam/apps/112233/capsule_sm_120.jpg",
            "https://cdn.akamai.steamstatic.com/steam/apps/112233/header.jpg"
        ),
        # Non-steam URL
        (
            "https://images.gamerpower.com/giveaway/1.jpg",
            "https://images.gamerpower.com/giveaway/1.jpg"
        ),
        # None input
        (None, None)
    ]

    for input_url, expected in test_cases:
        result = _sanitize_steam_image_url(input_url)
        print(f"Input: {input_url}")
        print(f"Result: {result}")
        assert result == expected
        print("PASS")
        print("-" * 20)

def test_store_icons():
    stores_to_check = ["Steam", "Epic Games Store", "GOG", "Itch.io", "IndieGala", "Ubisoft Store"]

    for store_name in stores_to_check:
        mapped = map_store(store_name)
        icon_url = mapped["store_icon_url"]
        print(f"Store: {store_name}")
        print(f"Icon: {icon_url}")
        assert "google.com/s2/favicons" in icon_url
        assert "wikimedia" not in icon_url
        print("PASS")
        print("-" * 20)

if __name__ == "__main__":
    print("Testing Steam URL Rewrite...")
    test_steam_url_rewrite()
    print("\nTesting Store Icons...")
    test_store_icons()
    print("\nAll verifications passed!")
