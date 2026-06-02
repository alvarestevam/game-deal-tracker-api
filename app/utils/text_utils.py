import re
import unicodedata

def normalize_title(title: str) -> str:
    """
    Normaliza o título do jogo para criar um slug único.
    - Converte para minúsculas.
    - Remove caracteres especiais (™, ®, ©).
    - Remove pontuações desnecessárias (vírgulas, dois pontos, traços).
    - Remove espaços extras.
    - Mantém palavras que definem versões (Deluxe, Gold, etc).
    """
    if not title:
        return ""

    # Converte para minúsculas
    text = title.lower()

    # Remove caracteres especiais específicos (TM, R, C)
    text = text.replace("™", "").replace("®", "").replace("©", "")

    # Normaliza acentos para evitar duplicados como "Ragnarök" e "Ragnarok"
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

    # Substitui pontuação (vírgulas, dois pontos, traços) por espaço
    text = re.sub(r"[,:\-]", " ", text)

    # Remove qualquer outro caractere que não seja letra, número ou espaço
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove espaços duplos e espaços nas extremidades
    text = " ".join(text.split())

    return text
