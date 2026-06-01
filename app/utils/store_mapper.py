from typing import Dict

STORE_DATA = {
    "Steam": {
        "name": "Steam",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png"
    },
    "Epic Games Store": {
        "name": "Epic Games Store",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Epic_Games_logo.svg/512px-Epic_Games_logo.svg.png"
    },
    "GOG": {
        "name": "GOG",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/GOG.com_logo.svg/512px-GOG.com_logo.svg.png"
    },
    "Itch.io": {
        "name": "Itch.io",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Itch.io_logo.svg/512px-Itch.io_logo.svg.png"
    },
    "IndieGala": {
        "name": "IndieGala",
        "store_icon_url": "https://www.cheapshark.com/img/stores/logos/29.png"
    },
    "PlayStation": {
        "name": "PlayStation Store",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Playstation_logo_colour.svg/512px-Playstation_logo_colour.svg.png"
    },
    "Xbox": {
        "name": "Xbox Store",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Xbox_logo_%282019%29.svg/512px-Xbox_logo_%282019%29.svg.png"
    },
    "Nintendo": {
        "name": "Nintendo eShop",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Nintendo.svg/512px-Nintendo.svg.png"
    },
    "Humble Store": {
        "name": "Humble Store",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Humble_Bundle_logo.svg/512px-Humble_Bundle_logo.svg.png"
    },
    "Green Man Gaming": {
        "name": "Green Man Gaming",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Green_Man_Gaming_logo.png/512px-Green_Man_Gaming_logo.png"
    },
    "Direct2Drive": {
        "name": "Direct2Drive",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/Direct2Drive_logo.svg/512px-Direct2Drive_logo.svg.png"
    },
    "DLGamer": {
        "name": "DLGamer",
        "store_icon_url": "https://www.cheapshark.com/img/stores/banners/32.png"
    },
    "Nuuvem": {
        "name": "Nuuvem",
        "store_icon_url": "https://assets.nuuvem.com/assets/fe/images/nuuvem_logo-ab61245ad5.png"
    },
    "Fanatical": {
        "name": "Fanatical",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/en/thumb/4/41/Fanatical_Logo.svg/512px-Fanatical_Logo.svg.png"
    },
    "Ubisoft Store": {
        "name": "Ubisoft Store",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Ubisoft_logo.svg/512px-Ubisoft_logo.svg.png"
    },
    "Gamesplanet": {
        "name": "Gamesplanet",
        "store_icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Logo_GamesPlanet.png/512px-Logo_GamesPlanet.png"
    },
    "Default": {
        "name": "Other Store",
        "store_icon_url": "https://cdn-icons-png.flaticon.com/512/5260/5260478.png"
    }
}

CHEAPSHARK_MAP = {
    "1": "Steam",
    "2": "Green Man Gaming",
    "3": "GOG",
    "7": "Direct2Drive",
    "11": "Humble Store",
    "15": "DLGamer",
    "21": "Nuuvem",
    "23": "Fanatical",
    "25": "Epic Games Store",
    "27": "Ubisoft Store",
    "35": "Gamesplanet"
}

SUBSTRING_MAP = {
    "steam": "Steam",
    "epic": "Epic Games Store",
    "gog": "GOG",
    "itch.io": "Itch.io",
    "indiegala": "IndieGala",
    "playstation": "PlayStation",
    "xbox": "Xbox",
    "nintendo": "Nintendo",
    "humble": "Humble Store",
    "greenman": "Green Man Gaming",
    "direct2drive": "Direct2Drive",
    "dlgamer": "DLGamer",
    "nuuvem": "Nuuvem",
    "fanatical": "Fanatical",
    "ubisoft": "Ubisoft Store",
    "uplay": "Ubisoft Store",
    "gamesplanet": "Gamesplanet"
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
        "store_icon_url": STORE_DATA["Default"]["store_icon_url"]
    }
