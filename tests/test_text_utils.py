from app.utils.text_utils import normalize_title

def test_normalize_title_basic():
    assert normalize_title("God of War") == "god of war"

def test_normalize_title_special_chars():
    assert normalize_title("God of War™") == "god of war"
    assert normalize_title("Game®") == "game"
    assert normalize_title("Company©") == "company"

def test_normalize_title_punctuation():
    assert normalize_title("Cyberpunk 2077: Phantom Liberty") == "cyberpunk 2077 phantom liberty"
    assert normalize_title("Counter-Strike 2") == "counter strike 2"
    assert normalize_title("Game, The") == "game the"

def test_normalize_title_extra_spaces():
    assert normalize_title("  Elden   Ring  ") == "elden ring"

def test_normalize_title_accented_chars():
    assert normalize_title("Ragnarök") == "ragnarok"
    assert normalize_title("Pokémon") == "pokemon"

def test_normalize_title_preserves_versions():
    assert normalize_title("Starfield Digital Premium Edition") == "starfield digital premium edition"
    assert normalize_title("Resident Evil 4 Deluxe Edition") == "resident evil 4 deluxe edition"
    assert normalize_title("Street Fighter 6 Ultimate Edition") == "street fighter 6 ultimate edition"
    assert normalize_title("The Sims 4 Gold Edition") == "the sims 4 gold edition"

def test_normalize_title_empty():
    assert normalize_title("") == ""
    assert normalize_title(None) == ""
