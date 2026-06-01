from typing import Dict

STORE_DATA = {
    "Steam": {
        "name": "Steam",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png"
    },
    "Epic Games": {
        "name": "Epic Games Store",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/512px-Epic_Games_logo.svg.png"
    },
    "GOG": {
        "name": "GOG",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/GOG.com_logo.svg/512px-GOG.com_logo.svg.png"
    },
    "Itch.io": {
        "name": "Itch.io",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Itch.io_logo.svg/512px-Itch.io_logo.svg.png"
    },
    "IndieGala": {
        "name": "IndieGala",
        "icon": "https://upload.wikimedia.org/wikipedia/en/thumb/8/8a/Indie_Gala_logo.png/220px-Indie_Gala_logo.png"
    },
    "PlayStation": {
        "name": "PlayStation Store",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Playstation_logo_colour.svg/512px-Playstation_logo_colour.svg.png"
    },
    "Xbox": {
        "name": "Xbox Store",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Xbox_logo_%282019%29.svg/512px-Xbox_logo_%282019%29.svg.png"
    },
    "Nintendo": {
        "name": "Nintendo eShop",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Nintendo.svg/512px-Nintendo.svg.png"
    },
    "Humble": {
        "name": "Humble Store",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Humble_Bundle_logo.svg/512px-Humble_Bundle_logo.svg.png"
    },
    "GreenManGaming": {
        "name": "Green Man Gaming",
        "icon": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Green_Man_Gaming_logo.png/250px-Green_Man_Gaming_logo.png"
    },
    "Default": {
        "name": "Other Store",
        "icon": "https://cdn-icons-png.flaticon.com/512/5260/5260478.png"
    }
}

CHEAPSHARK_MAP = {
    "1": "Steam",
    "2": "GreenManGaming",
    "11": "Humble"
}

SUBSTRING_MAP = {
    "epic": "Epic Games",
    "gog": "GOG",
    "itch.io": "Itch.io",
    "indiegala": "IndieGala",
    "playstation": "PlayStation",
    "xbox": "Xbox",
    "nintendo": "Nintendo",
    "humble": "Humble",
    "steam": "Steam",
    "greenman": "GreenManGaming"
}

def map_store(store_input: str | None) -> Dict[str, str]:
    """
    Maps a raw store name or ID to a clean name and icon URL.
    """
    if not store_input:
        return STORE_DATA["Default"]

    # 1. Aggressive cleaning of parasitic substrings
    parasitic_substrings = ["PC, ", ", DRM-Free", ", Steam Key", ", Windows"]
    clean_name = store_input
    for parasitic in parasitic_substrings:
        clean_name = clean_name.replace(parasitic, "")

    # Trim potential trailing commas or spaces left after replacement
    clean_name = clean_name.strip().strip(",").strip()

    # 2. Treat CheapShark numeric IDs
    if clean_name in CHEAPSHARK_MAP:
        return STORE_DATA[CHEAPSHARK_MAP[clean_name]]

    # 3. Substring detection (GamerPower/ITAD/Others)
    lower_input = clean_name.lower()
    for key, store_key in SUBSTRING_MAP.items():
        if key in lower_input:
            return STORE_DATA[store_key]

    # 4. Fallback: use cleaned name but generic icon
    return {
        "name": clean_name,
        "icon": STORE_DATA["Default"]["icon"]
    }
