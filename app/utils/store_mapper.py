from typing import Dict

STORE_DATA = {
    "Steam": {
        "name": "Steam",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=steampowered.com"
    },
    "Epic Games Store": {
        "name": "Epic Games Store",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=epicgames.com"
    },
    "GOG": {
        "name": "GOG",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=gog.com"
    },
    "Itch.io": {
        "name": "Itch.io",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=itch.io"
    },
    "IndieGala": {
        "name": "IndieGala",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=indiegala.com"
    },
    "PlayStation": {
        "name": "PlayStation Store",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=playstation.com"
    },
    "Xbox": {
        "name": "Xbox Store",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=xbox.com"
    },
    "Nintendo": {
        "name": "Nintendo eShop",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=nintendo.com"
    },
    "Humble Store": {
        "name": "Humble Store",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=humblebundle.com"
    },
    "Green Man Gaming": {
        "name": "Green Man Gaming",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=greenmangaming.com"
    },
    "Direct2Drive": {
        "name": "Direct2Drive",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=direct2drive.com"
    },
    "DLGamer": {
        "name": "DLGamer",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=dlgamer.com"
    },
    "Nuuvem": {
        "name": "Nuuvem",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=nuuvem.com"
    },
    "Fanatical": {
        "name": "Fanatical",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=fanatical.com"
    },
    "Ubisoft Store": {
        "name": "Ubisoft Store",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=ubisoft.com"
    },
    "Gamesplanet": {
        "name": "Gamesplanet",
        "store_icon_url": "https://www.google.com/s2/favicons?sz=128&domain=gamesplanet.com"
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
